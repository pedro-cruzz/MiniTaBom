import tkinter as tk
from tkinter import ttk


class ContingencyDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title('Qui-quadrado de associação')
        self.transient(parent)
        self.resizable(False, False)
        ttk.Label(self, text='Tabela de contingência e qui-quadrado', style='Title.TLabel').pack(fill='x')
        body = ttk.Frame(self, padding=16)
        body.pack(fill='both', expand=True)
        self.tabs = ttk.Notebook(body)
        self.tabs.pack(fill='both', expand=True)
        data, options = ttk.Frame(self.tabs, padding=16), ttk.Frame(self.tabs, padding=16)
        self.tabs.add(data, text='Dados', image=parent.icons['table'], compound='left')
        self.tabs.add(options, text='Exibição', image=parent.icons['options'], compound='left')
        self.source = ttk.Combobox(data, state='readonly', width=48,
                                  values=['Dados categóricos em duas colunas', 'Tabela de contagens em colunas'])
        self.source.current(0)
        self.source.grid(row=0, column=0, sticky='ew', pady=(0, 12))
        self.source.bind('<<ComboboxSelected>>', lambda e: self.toggle_source())
        self.raw, self.matrix = ttk.Frame(data), ttk.Frame(data)
        self.raw.grid(row=1, column=0, sticky='ew')
        self.matrix.grid(row=1, column=0, sticky='ew')
        self.row_column = self.picker(self.raw, 0, 'Variável de linha:', 0)
        self.column_column = self.picker(self.raw, 1, 'Variável de coluna:', 1)
        self.count_column = self.picker(self.raw, 2, 'Frequências (opcional):', 0, optional=True)
        ttk.Label(self.raw, text='Sem frequências, cada linha corresponde a uma observação.\n'
                  'Categorias são textos exatos aparados; vazio e * são ausentes.', foreground='#536477').grid(
                      row=3, column=0, columnspan=2, sticky='w', pady=(12, 0))
        ttk.Label(self.matrix, text='Colunas com contagens (Ctrl/Shift para selecionar):').pack(anchor='w')
        selection = ttk.Frame(self.matrix)
        selection.pack(fill='both', pady=(7, 12))
        self.columns = tk.Listbox(selection, selectmode='extended', exportselection=False, height=7,
                                  width=45, activestyle='none', font=('Segoe UI', 9))
        scroll = ttk.Scrollbar(selection, orient='vertical', command=self.columns.yview)
        self.columns.configure(yscrollcommand=scroll.set)
        self.columns.pack(side='left', fill='both', expand=True)
        scroll.pack(side='right', fill='y')
        for i, label in enumerate(parent.headers):
            self.columns.insert('end', f'C{i + 1}  {label}')
        label_frame = ttk.Frame(self.matrix)
        label_frame.pack(fill='x')
        self.label_column = self.picker(label_frame, 0, 'Rótulos das linhas:', 0, optional=True)
        ttk.Label(self.matrix, text='Não inclua totais marginais. Informe 0 para contagens nulas.\n'
                  'Linhas com todas as contagens ausentes são omitidas.', foreground='#536477').pack(anchor='w', pady=(10, 0))
        self.show_expected = tk.BooleanVar(self, value=True)
        self.show_residuals = tk.BooleanVar(self, value=False)
        self.show_contributions = tk.BooleanVar(self, value=False)
        self.show_percentages = tk.BooleanVar(self, value=False)
        for label, variable in [('Frequências esperadas', self.show_expected),
                                ('Resíduos brutos, padronizados e ajustados', self.show_residuals),
                                ('Contribuições de cada célula ao qui-quadrado', self.show_contributions),
                                ('Percentuais por linha, coluna e total', self.show_percentages)]:
            ttk.Checkbutton(options, text=label, variable=variable).pack(anchor='w', pady=8)
        ttk.Label(options, text='Pearson e razão de verossimilhanças, sem correção de Yates.\n'
                  'Em tabelas 2×2, também apresenta Fisher bilateral.', foreground='#536477').pack(anchor='w', pady=(12, 0))
        actions = ttk.Frame(body)
        actions.pack(fill='x', pady=(16, 0))
        ttk.Button(actions, text='Cancelar', command=self.destroy).pack(side='right', padx=(8, 0))
        ttk.Button(actions, text='Calcular', style='Accent.TButton', command=self.submit).pack(side='right')
        self.bind('<Escape>', lambda e: self.destroy())
        self.bind('<Return>', lambda e: self.submit())
        self.toggle_source()
        parent.center_dialog(self)
        self.grab_set()

    def picker(self, frame, row, label, default, optional=False):
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky='w', padx=(0, 16), pady=7)
        values = [f'C{i + 1}  {name}' for i, name in enumerate(self.parent.headers)]
        if optional:
            values.insert(0, '(Nenhuma)')
        picker = ttk.Combobox(frame, state='readonly', width=29, values=values)
        picker.current(min(default, len(values) - 1))
        picker.grid(row=row, column=1, sticky='w')
        return picker

    def toggle_source(self):
        self.raw.grid() if self.source.current() == 0 else self.raw.grid_remove()
        self.matrix.grid_remove() if self.source.current() == 0 else self.matrix.grid()

    def submit(self):
        options = dict(show_expected=self.show_expected.get(), show_residuals=self.show_residuals.get(),
                       show_contributions=self.show_contributions.get(), show_percentages=self.show_percentages.get())
        if self.source.current() == 0:
            options.update(row_column=self.row_column.current(), column_column=self.column_column.current(),
                           count_column=self.count_column.current() - 1 if self.count_column.current() > 0 else None)
        else:
            options.update(columns=list(self.columns.curselection()),
                           label_column=self.label_column.current() - 1 if self.label_column.current() > 0 else None)
        if self.parent.run_contingency('categorical' if self.source.current() == 0 else 'matrix', **options):
            self.destroy()
