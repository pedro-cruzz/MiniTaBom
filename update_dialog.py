"""Consulta em thread; todos os acessos a Tk ficam na thread principal."""
from queue import Empty, Queue
import threading
import tkinter as tk
from tkinter import ttk
import webbrowser

from updates import check_latest, configured_repository, load_metadata, normalize_repository, save_repository


class UpdateDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title('Verificar atualizações — MiniTaBom')
        self.transient(parent)
        self.resizable(False, False)
        self.results = Queue()
        self.poll_id = None
        self.release_url = None
        body = ttk.Frame(self, padding=18)
        body.pack(fill='both', expand=True)
        self.current_version = load_metadata()['version']
        ttk.Label(body, text=f'Versão instalada: {self.current_version}', style='Title.TLabel').pack(anchor='w')
        ttk.Label(body, text='Repositório do MiniTaBom no GitHub:').pack(anchor='w', pady=(16, 5))
        self.repository = ttk.Entry(body, width=60)
        self.repository.pack(fill='x')
        try:
            self.repository.insert(0, configured_repository())
            note = 'Clique em Verificar para consultar a última Release estável.'
        except (ValueError, OSError, KeyError):
            note = 'Confira o repositório informado antes de verificar.'
        self.message = ttk.Label(body, text=note, wraplength=460)
        self.message.pack(anchor='w', pady=14)
        actions = ttk.Frame(body)
        actions.pack(fill='x')
        self.check_button = ttk.Button(actions, text='Verificar', command=self.check)
        self.check_button.pack(side='left')
        self.open_button = ttk.Button(actions, text='Abrir página da versão', command=self.open_release, state='disabled')
        self.open_button.pack(side='left', padx=8)
        ttk.Button(actions, text='Fechar', command=self.destroy).pack(side='right')
        self.bind('<Escape>', lambda event: self.destroy())
        self.bind('<Return>', lambda event: self.check())
        parent.center_dialog(self)
        self.repository.focus_set()

    def check(self):
        if str(self.check_button.cget('state')) == 'disabled':
            return
        try:
            repository = normalize_repository(self.repository.get())
            save_repository(repository)
        except (ValueError, OSError) as error:
            self.message.configure(text=str(error))
            return
        self.release_url = None
        self.open_button.configure(state='disabled')
        self.check_button.configure(state='disabled')
        self.repository.configure(state='disabled')
        self.message.configure(text='Consultando o GitHub…')
        threading.Thread(target=self.worker, args=(repository,), daemon=True).start()
        self.poll_id = self.after(100, self.poll)

    def worker(self, repository):
        try:
            self.results.put((True, check_latest(repository, self.current_version)))
        except Exception as error:
            self.results.put((False, str(error)))

    def poll(self):
        self.poll_id = None
        try:
            success, result = self.results.get_nowait()
        except Empty:
            self.poll_id = self.after(100, self.poll)
            return
        self.check_button.configure(state='normal')
        self.repository.configure(state='normal')
        if success:
            self.release_url = result['url']
            self.open_button.configure(state='normal')
            self.message.configure(text=(f"Nova versão disponível: {result['latest']}. Abra a página para baixar o pacote."
                if result['newer'] else f"Você já está atualizado em relação à Release publicada ({result['latest']})."))
        else:
            self.message.configure(text=result)

    def open_release(self):
        if self.release_url:
            try:
                if not webbrowser.open(self.release_url):
                    self.message.configure(text='Abra este endereço no navegador: ' + self.release_url)
            except webbrowser.Error:
                self.message.configure(text='Abra este endereço no navegador: ' + self.release_url)

    def destroy(self):
        if self.poll_id is not None:
            self.after_cancel(self.poll_id)
            self.poll_id = None
        super().destroy()
