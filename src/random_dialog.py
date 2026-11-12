import tkinter as tk
from tkinter import ttk, messagebox

from random_contract import RANDOM_DISTRIBUTIONS


class RandomDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.app = parent
        self.title('Gerar dados aleatórios')
        self.transient(parent)
        self.resizable(False, False)
        body = ttk.Frame(self, padding=16)
        body.pack(fill='both', expand=True)
        ttk.Label(body, text='Distribuição:').grid(row=0, column=0, sticky='w', pady=6)
        self.distribution = ttk.Combobox(body, values=list(RANDOM_DISTRIBUTIONS), state='readonly', width=34)
        self.distribution.current(0)
        self.distribution.grid(row=0, column=1, sticky='ew', padx=(12, 0))
        self.distribution.bind('<<ComboboxSelected>>', self.update_parameters)
        self.parameter_frame = ttk.LabelFrame(body, text='Parâmetros', padding=10)
        self.parameter_frame.grid(row=1, column=0, columnspan=2, sticky='ew', pady=10)
        self.parameters = {}
        self.update_parameters()
        for row, key, label, default in [(2, 'row_count', 'Linhas por coluna:', '100'),
                                         (3, 'column_count', 'Quantidade de colunas:', '1'),
                                         (4, 'base_name', 'Nome das novas colunas:', 'Aleatorio'),
                                         (5, 'seed', 'Semente (opcional):', '')]:
            ttk.Label(body, text=label).grid(row=row, column=0, sticky='w', pady=6)
            entry = ttk.Entry(body, width=35)
            entry.insert(0, default)
            entry.grid(row=row, column=1, sticky='ew', padx=(12, 0))
            setattr(self, key, entry)
        ttk.Label(body, text='Semente: inteiro de 0 a 2¹²⁸−1. Vazio cria e registra uma semente.\n'
                  'Os dados entram em novas colunas da planilha ativa. Ctrl+Z desfaz.\n'
                  'Para repetir os valores depois, use o Histórico de análises.',
                  wraplength=465).grid(row=6, column=0, columnspan=2, sticky='w', pady=12)
        actions = ttk.Frame(body)
        actions.grid(row=7, column=0, columnspan=2, sticky='e')
        ttk.Button(actions, text='Gerar', command=self.submit).pack(side='left', padx=6)
        ttk.Button(actions, text='Cancelar', command=self.destroy).pack(side='left')
        self.bind('<Escape>', lambda event: self.destroy())
        self.bind('<Return>', lambda event: self.submit())
        parent.center_dialog(self)
        self.grab_set()

    def update_parameters(self, event=None):
        for widget in self.parameter_frame.winfo_children():
            widget.destroy()
        self.parameters = {}
        for row, (key, label, value) in enumerate(RANDOM_DISTRIBUTIONS[self.distribution.get()]):
            ttk.Label(self.parameter_frame, text=label + ':').grid(row=row, column=0, sticky='w', pady=4, padx=(0, 15))
            entry = ttk.Entry(self.parameter_frame, width=20)
            entry.insert(0, str(value))
            entry.grid(row=row, column=1, sticky='w', pady=4)
            self.parameters[key] = entry

    def submit(self):
        try:
            parameters = {key: float(field.get().strip().replace(',', '.')) for key, field in self.parameters.items()}
            row_count = int(self.row_count.get().strip())
            column_count = int(self.column_count.get().strip())
            seed_text = self.seed.get().strip()
            seed = int(seed_text) if seed_text else None
        except ValueError:
            messagebox.showerror('Valores inválidos', 'Confira os parâmetros. Linhas, colunas e semente devem ser inteiros.', parent=self)
            return
        if self.app.start_random(self.distribution.get(), parameters, row_count=row_count, column_count=column_count,
                               seed=seed, base_name=self.base_name.get()):
            self.destroy()
