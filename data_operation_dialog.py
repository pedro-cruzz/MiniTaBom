import tkinter as tk
from tkinter import ttk

from data_operations import unique_name


DATA_TITLES = {'sort': 'Ordenar linhas', 'stack': 'Empilhar colunas', 'unstack': 'Desempilhar por grupo'}


class DataOperationDialog(tk.Toplevel):
    def __init__(self, parent, operation):
        super().__init__(parent)
        self.parent, self.operation = parent, operation
        self.title(DATA_TITLES[operation])
        self.transient(parent)
        self.resizable(False, False)
        ttk.Label(self, text=DATA_TITLES[operation], style='Title.TLabel').pack(fill='x')
        body = ttk.Frame(self, padding=18)
        body.pack(fill='both', expand=True)
        tabs = ttk.Notebook(body)
        tabs.pack(fill='both', expand=True)
        data, options = ttk.Frame(tabs, padding=16), ttk.Frame(tabs, padding=16)
        tabs.add(data, text='Dados', image=parent.icons['table'], compound='left')
        tabs.add(options, text='Opções', image=parent.icons['options'], compound='left')
        labels = [f'C{i + 1}  {name}' for i, name in enumerate(parent.headers)]
        self.omit_missing, self.include_missing = tk.BooleanVar(self), tk.BooleanVar(self)
        self.keys, self.types, self.directions = [], [], []
        if operation == 'sort':
            for col, title in enumerate(['Prioridade', 'Coluna', 'Tipo', 'Ordem']):
                ttk.Label(data, text=title).grid(row=0, column=col, sticky='w', padx=5, pady=(0, 8))
            for i in range(3):
                ttk.Label(data, text=str(i + 1)).grid(row=i + 1, column=0, padx=5)
                key = ttk.Combobox(data, state='readonly', width=26, values=['Não usar'] + labels)
                key.current(max(0, parent.column.current()) + 1 if i == 0 else 0)
                key.grid(row=i + 1, column=1, padx=5, pady=6)
                mode = ttk.Combobox(data, state='readonly', width=13, values=['Automático', 'Numérico', 'Texto'])
                mode.current(0)
                mode.grid(row=i + 1, column=2, padx=5)
                direction = ttk.Combobox(data, state='readonly', width=13, values=['Crescente', 'Decrescente'])
                direction.current(0)
                direction.grid(row=i + 1, column=3, padx=5)
                self.keys.append(key)
                self.types.append(mode)
                self.directions.append(direction)
            self.missing_last = tk.BooleanVar(self, value=True)
            self.case_sensitive = tk.BooleanVar(self, value=True)
            ttk.Checkbutton(options, text='Ausentes no final, nas duas direções', variable=self.missing_last).pack(anchor='w', pady=6)
            ttk.Checkbutton(options, text='Distinguir maiúsculas e minúsculas no texto', variable=self.case_sensitive).pack(anchor='w', pady=6)
            info = 'Todas as colunas são ordenadas juntas. Automático usa números quando todos os valores não ausentes da chave são numéricos finitos.'
        elif operation == 'stack':
            ttk.Label(data, text='Colunas de origem (Ctrl/Shift para várias):').pack(anchor='w')
            frame = ttk.Frame(data)
            frame.pack(fill='both', expand=True, pady=8)
            self.columns = tk.Listbox(frame, selectmode='extended', exportselection=False, height=9, width=56)
            self.columns.pack(side='left', fill='both', expand=True)
            scroll = ttk.Scrollbar(frame, command=self.columns.yview)
            scroll.pack(side='right', fill='y')
            self.columns.configure(yscrollcommand=scroll.set)
            for label in labels:
                self.columns.insert('end', label)
            self.columns.selection_set(max(0, parent.column.current()))
            used = set(parent.headers)
            value = unique_name('Valor', used)
            used.add(value)
            origin = unique_name('Origem', used)
            self.value_name = self.entry(options, 0, 'Coluna de valores:', value)
            self.label_name = self.entry(options, 1, 'Coluna de origem:', origin)
            ttk.Checkbutton(options, text='Omitir valores ausentes', variable=self.omit_missing).grid(row=2, column=0, columnspan=2, sticky='w', pady=8)
            info = 'Adiciona duas colunas. Empilha uma coluna inteira de cada vez, na ordem das colunas selecionadas. As fontes são preservadas.'
        else:
            self.value_column = self.combo(data, 0, 'Valores:', labels)
            self.value_column.current(max(0, parent.column.current()))
            self.group_column = self.combo(data, 1, 'Por variável de grupo:', labels)
            self.group_column.current(1 if len(labels) > 1 and self.value_column.current() != 1 else 0)
            self.prefix = self.entry(options, 0, 'Prefixo das novas colunas:', 'Separado')
            ttk.Checkbutton(options, text='Omitir valores ausentes', variable=self.omit_missing).grid(row=1, column=0, columnspan=2, sticky='w', pady=8)
            ttk.Checkbutton(options, text='Incluir grupos ausentes em uma coluna', variable=self.include_missing).grid(row=2, column=0, columnspan=2, sticky='w', pady=8)
            info = 'Adiciona uma coluna por grupo, na ordem de aparição. Dentro de cada grupo, mantém a ordem das linhas. As fontes são preservadas.'
        ttk.Label(body, text=info, wraplength=540, foreground='#536477').pack(fill='x', pady=(14, 0))
        actions = ttk.Frame(body)
        actions.pack(fill='x', pady=(16, 0))
        ttk.Button(actions, text='Cancelar', command=self.destroy).pack(side='right', padx=(8, 0))
        ttk.Button(actions, text='Aplicar', style='Accent.TButton', command=self.submit).pack(side='right')
        self.bind('<Escape>', lambda e: self.destroy())
        self.bind('<Return>', lambda e: self.submit())
        parent.center_dialog(self)
        self.grab_set()

    @staticmethod
    def combo(frame, row, label, values):
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky='w', padx=(0, 16), pady=8)
        widget = ttk.Combobox(frame, state='readonly', width=36, values=values)
        widget.grid(row=row, column=1, sticky='w')
        return widget

    @staticmethod
    def entry(frame, row, label, value):
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky='w', padx=(0, 16), pady=8)
        widget = ttk.Entry(frame, width=30)
        widget.insert(0, value)
        widget.grid(row=row, column=1, sticky='w')
        return widget

    def submit(self):
        if self.operation == 'sort':
            active = [i for i, key in enumerate(self.keys) if key.current() > 0]
            options = dict(keys=[self.keys[i].current() - 1 for i in active],
                           types=[('auto', 'numeric', 'text')[self.types[i].current()] for i in active],
                           descending=[self.directions[i].current() == 1 for i in active],
                           missing_last=self.missing_last.get(), case_sensitive=self.case_sensitive.get())
        elif self.operation == 'stack':
            options = dict(columns=list(self.columns.curselection()), value_name=self.value_name.get(),
                           label_name=self.label_name.get(), omit_missing=self.omit_missing.get())
        else:
            options = dict(value_column=self.value_column.current(), group_column=self.group_column.current(),
                           prefix=self.prefix.get(), omit_missing=self.omit_missing.get(),
                           include_missing_groups=self.include_missing.get())
        if self.parent.run_data_operation(self.operation, **options):
            self.destroy()
