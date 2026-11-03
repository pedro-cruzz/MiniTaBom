"""Seleção das respostas, grupos e medidas de estatística descritiva."""
import tkinter as tk
from tkinter import ttk
from core import DESCRIPTIVE_STATISTICS


class DescriptiveDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.app = parent
        self.title('Exibir estatísticas descritivas')
        self.transient(parent)
        self.resizable(False, False)
        body = ttk.Frame(self, padding=12)
        body.pack(fill='both', expand=True)
        notebook = ttk.Notebook(body)
        notebook.pack(fill='both', expand=True)
        data = ttk.Frame(notebook, padding=12)
        stats = ttk.Frame(notebook, padding=12)
        notebook.add(data, text='Dados e grupos', image=parent.icons['table'], compound='left')
        notebook.add(stats, text='Estatísticas', image=parent.icons['summary'], compound='left')
        self.variables = self.column_list(data, parent.headers, 'Variáveis numéricas:', 0)
        self.groups = self.column_list(data, parent.headers, 'Por variáveis (opcional):', 1)
        self.variables.selection_set(max(0, parent.column.current()))
        ttk.Label(data, text='Use Ctrl ou Shift para selecionar várias colunas. Sem grupos, o resumo usa todas as linhas.').grid(
            row=2, column=0, columnspan=2, sticky='w', pady=(10, 8))
        self.include_missing = tk.BooleanVar(self, value=False)
        self.include_empty = tk.BooleanVar(self, value=False)
        self.missing_check = ttk.Checkbutton(data, text='Incluir valores de grupo ausentes como um grupo separado', variable=self.include_missing)
        self.missing_check.grid(row=3, column=0, columnspan=2, sticky='w', pady=3)
        self.empty_check = ttk.Checkbutton(data, text='Incluir combinações sem observações entre os grupos selecionados', variable=self.include_empty)
        self.empty_check.grid(row=4, column=0, columnspan=2, sticky='w', pady=3)
        self.groups.bind('<<ListboxSelect>>', self.update_options)
        self.update_options()
        self.checks = {}
        defaults = {'N', 'Ausentes', 'Média', 'Erro padrão', 'Desvio padrão amostral',
                    'Mínimo', 'Q1', 'Mediana', 'Q3', 'Máximo'}
        rows = (len(DESCRIPTIVE_STATISTICS) + 1) // 2
        for index, key in enumerate(DESCRIPTIVE_STATISTICS):
            self.checks[key] = tk.BooleanVar(self, value=key in defaults)
            ttk.Checkbutton(stats, text=key, variable=self.checks[key]).grid(
                row=index % rows, column=index // rows, sticky='w', padx=8, pady=2)
        ttk.Button(stats, text='Selecionar todas', command=lambda: self.choose_all(True)).grid(row=rows, column=0, pady=(8, 0))
        ttk.Button(stats, text='Desmarcar todas', command=lambda: self.choose_all(False)).grid(row=rows, column=1, pady=(8, 0))
        actions = ttk.Frame(body)
        actions.pack(fill='x', pady=(12, 0))
        ttk.Button(actions, text='Cancelar', command=self.destroy).pack(side='right')
        ttk.Button(actions, text='OK', command=self.submit).pack(side='right', padx=6)
        self.bind('<Escape>', lambda event: self.destroy())
        self.bind('<Return>', lambda event: self.submit())
        parent.center_dialog(self)
        self.variables.focus_set()
        self.grab_set()

    @staticmethod
    def column_list(parent, headers, label, column):
        frame = ttk.Frame(parent)
        frame.grid(row=0, column=column, sticky='nsew', padx=(0, 12) if column == 0 else (0, 0))
        ttk.Label(frame, text=label).pack(anchor='w', pady=(0, 5))
        field = ttk.Frame(frame)
        field.pack(fill='both', expand=True)
        listing = tk.Listbox(field, selectmode='extended', exportselection=False, height=10, width=34,
                             font=('Segoe UI', 9), borderwidth=1, relief='sunken',
                             selectbackground='#2d6495', selectforeground='white', activestyle='none')
        scroll = ttk.Scrollbar(field, orient='vertical', command=listing.yview)
        listing.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right', fill='y')
        listing.pack(fill='both', expand=True)
        for index, name in enumerate(headers):
            listing.insert('end', f'C{index + 1}  {name}')
        return listing

    def update_options(self, event=None):
        count = len(self.groups.curselection())
        self.missing_check.configure(state='normal' if count else 'disabled')
        self.empty_check.configure(state='normal' if count > 1 else 'disabled')
        if count == 0:
            self.include_missing.set(False)
        if count < 2:
            self.include_empty.set(False)

    def choose_all(self, value):
        for selected in self.checks.values():
            selected.set(value)

    def submit(self):
        selected = [key for key in DESCRIPTIVE_STATISTICS if self.checks[key].get()]
        if self.app.run_summary(list(self.variables.curselection()), selected,
                                by=list(self.groups.curselection()),
                                include_missing=self.include_missing.get(),
                                include_empty=self.include_empty.get()):
            self.destroy()
