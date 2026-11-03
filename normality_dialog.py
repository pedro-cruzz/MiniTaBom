import tkinter as tk
from tkinter import ttk


class NormalityDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title('Teste de normalidade')
        self.transient(parent)
        self.resizable(False, False)
        ttk.Label(self, text='Teste de normalidade', style='Title.TLabel').pack(fill='x')
        body = ttk.Frame(self, padding=16)
        body.pack(fill='both', expand=True)
        self.tabs = ttk.Notebook(body)
        self.tabs.pack(fill='both', expand=True)
        data = ttk.Frame(self.tabs, padding=16)
        self.tabs.add(data, text='Dados e método', image=parent.icons['distribution'], compound='left')
        ttk.Label(data, text='Amostra:').grid(row=0, column=0, sticky='w', padx=(0, 16), pady=8)
        self.column = ttk.Combobox(data, state='readonly', width=36,
                                  values=[f'C{i + 1}  {name}' for i, name in enumerate(parent.headers)])
        self.column.current(max(0, parent.column.current()))
        self.column.grid(row=0, column=1, sticky='w')
        ttk.Label(data, text='Método:').grid(row=1, column=0, sticky='w', pady=8)
        ttk.Label(data, text='Anderson–Darling (normal, parâmetros estimados)').grid(row=1, column=1, sticky='w')
        ttk.Label(data, text='Vazio e * são omitidos. A amostra deve conter ao menos três números\n'
                  'e ter desvio padrão positivo.', foreground='#536477').grid(
                      row=2, column=0, columnspan=2, sticky='w', pady=(12, 0))
        actions = ttk.Frame(body)
        actions.pack(fill='x', pady=(16, 0))
        ttk.Button(actions, text='Cancelar', command=self.destroy).pack(side='right', padx=(8, 0))
        ttk.Button(actions, text='Calcular', style='Accent.TButton', command=self.submit).pack(side='right')
        self.bind('<Escape>', lambda e: self.destroy())
        self.bind('<Return>', lambda e: self.submit())
        parent.center_dialog(self)
        self.grab_set()

    def submit(self):
        if self.parent.run_normality(self.column.current()):
            self.destroy()
