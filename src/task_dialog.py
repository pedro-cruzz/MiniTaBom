"""Polling e callbacks de conclusão são executados somente na thread Tk."""
import tkinter as tk
from tkinter import ttk, messagebox

from background_tasks import BackgroundTask


class TaskDialog(tk.Toplevel):
    def __init__(self, parent, title, work, apply_result):
        super().__init__(parent)
        self.app = parent
        self.apply_result = apply_result
        self.poll_id = None
        self.finished = False
        self.task = None
        self.previous_grab = parent.grab_current()
        self.close_app_requested = False
        self.title(title)
        self.transient(parent)
        self.resizable(False, False)
        self.protocol('WM_DELETE_WINDOW', self.cancel)
        self.bind('<Escape>', lambda event: self.cancel())
        body = ttk.Frame(self, padding=18)
        body.pack(fill='both', expand=True)
        self.message = ttk.Label(body, text='Preparando…', width=62, wraplength=455)
        self.message.pack(anchor='w', pady=(0, 10))
        self.progress = ttk.Progressbar(body, maximum=100, mode='determinate', length=455)
        self.progress.pack(fill='x')
        self.percentage = ttk.Label(body, text='0%')
        self.percentage.pack(anchor='e', pady=(3, 8))
        ttk.Label(body, text='Os dados só serão aplicados quando a operação terminar.', wraplength=455).pack(anchor='w', pady=(0, 12))
        self.cancel_button = ttk.Button(body, text='Cancelar', command=self.cancel)
        self.cancel_button.pack(anchor='e')
        self.app.set_task_busy(True)
        self.app._task_window = self
        parent.center_dialog(self)
        self.grab_set()
        self.focus_set()
        try:
            self.task = BackgroundTask(work)
        except Exception:
            self.dispose()
            raise
        self.poll_id = self.after(40, self.poll)

    def cancel(self):
        if self.finished:
            return
        if self.task is not None:self.task.cancel()
        self.cancel_button.configure(text='Cancelando…', state='disabled')
        self.message.configure(text='Cancelando… aguarde o ponto de interrupção da operação.')

    def poll(self):
        self.poll_id = None
        if self.finished:
            return
        state = self.task.snapshot()
        if state['state'] != 'cancelling':
            self.message.configure(text=state['message'])
        self.progress.configure(value=100 * state['fraction'])
        self.percentage.configure(text=f"{int(100 * state['fraction'])}%")
        outcome = self.task.take_outcome()
        if outcome is None:
            self.poll_id = self.after(40, self.poll)
            return
        close_app = self.close_app_requested
        self.dispose()
        kind, value = outcome
        if kind == 'cancelled':
            self.app.status.set('Operação cancelada · dados preservados')
        elif kind == 'failed':
            self.app.status.set('Operação não concluída · dados preservados')
            messagebox.showerror('Não foi possível concluir', str(value), parent=self.app)
        else:
            try:
                if self.apply_result(value) is False:
                    self.app.status.set('Operação não aplicada · dados preservados')
            except (ValueError, ArithmeticError, OSError) as error:
                self.app.status.set('Resultado não aplicado · dados preservados')
                messagebox.showerror('Não foi possível aplicar o resultado', str(error), parent=self.app)
        if close_app:
            self.app.close()

    def dispose(self):
        if self.finished:
            return
        self.finished = True
        if self.poll_id is not None:
            self.after_cancel(self.poll_id)
            self.poll_id = None
        if getattr(self.app, '_task_window', None) is self:
            self.app._task_window = None
        self.app.set_task_busy(False)
        super().destroy()
        if self.previous_grab is not None and self.previous_grab.winfo_exists():
            self.previous_grab.grab_set()

    def destroy(self):
        # Fechar a aplicação descarta também um resultado que já esteja pronto.
        if not self.finished:
            if self.task is not None:self.task.cancel()
            self.dispose()
