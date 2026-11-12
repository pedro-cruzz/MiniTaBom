import time


def drain_task(app, timeout=10.):
    deadline = time.monotonic() + timeout
    while app._task_window is not None:
        app.update()
        if time.monotonic() >= deadline:
            raise AssertionError('A tarefa não concluiu: ' + str(app._task_window.task.snapshot()))
        time.sleep(.005)
    app.update_idletasks()
