"""Trabalho sem Tk; resultados só são entregues quando a interface os recolhe."""
import math
import threading


class TaskCancelled(Exception):
    pass


class TaskContext:
    def __init__(self, cancelled=None, reporter=None, start=0., end=1.):
        self.cancelled = cancelled if cancelled is not None else threading.Event()
        self.reporter = reporter
        self.start, self.end = start, end

    def checkpoint(self):
        if self.cancelled.is_set():
            raise TaskCancelled('Operação cancelada.')

    def report(self, fraction, message):
        self.checkpoint()
        if not math.isfinite(fraction) or not 0 <= fraction <= 1:
            raise ValueError('Progresso fora do intervalo de 0 a 1.')
        if self.reporter:
            self.reporter(self.start + (self.end - self.start) * fraction, str(message))

    def phase(self, start, end):
        if not 0 <= start <= end <= 1:
            raise ValueError('Fase de progresso inválida.')
        span = self.end - self.start
        return TaskContext(self.cancelled, self.reporter, self.start + span * start, self.start + span * end)


class BackgroundTask:
    """Uma thread e um slot de progresso, sem filas que cresçam com a entrada."""
    def __init__(self, work):
        self._lock = threading.Lock()
        self._cancelled = threading.Event()
        self._done = threading.Event()
        self._state = 'running'
        self._payload = None
        self._taken = False
        self._progress = (0., 'Preparando…')
        self.context = TaskContext(self._cancelled, self._report)
        self.thread = threading.Thread(target=self._run, args=(work,), name='MiniTaBom-task', daemon=True)
        self.thread.start()

    def _report(self, fraction, message):
        with self._lock:
            if fraction >= self._progress[0]:
                self._progress = (fraction, message)

    def _run(self, work):
        state, payload = 'failed', None
        try:
            self.context.checkpoint()
            payload = work(self.context)
            self.context.checkpoint()
            state = 'succeeded'
        except TaskCancelled:
            state, payload = 'cancelled', None
        except BaseException as error:
            payload = error
        finally:
            with self._lock:
                if self._cancelled.is_set():
                    state, payload = 'cancelled', None
                self._state, self._payload = state, payload
                self._done.set()

    def cancel(self):
        with self._lock:
            if self._taken:
                return False
            self._cancelled.set()
            if self._done.is_set():
                self._state, self._payload = 'cancelled', None
            else:
                self._state = 'cancelling'
            return True

    def snapshot(self):
        with self._lock:
            return dict(state=self._state, done=self._done.is_set(), fraction=self._progress[0], message=self._progress[1])

    def take_outcome(self):
        with self._lock:
            if not self._done.is_set() or self._taken:
                return None
            self._taken = True
            outcome = self._state, self._payload
            self._payload = None
            return outcome
