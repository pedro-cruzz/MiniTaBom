import tkinter as tk
from tkinter import ttk

from xy_graphs import XY_TITLES


class XYGraphDialog(tk.Toplevel):
    def __init__(self, parent, kind):
        super().__init__(parent)
        self.parent, self.kind = parent, kind
        self.title(XY_TITLES[kind])
        self.transient(parent)
        self.resizable(False, False)
        ttk.Label(self, text=XY_TITLES[kind], style='Title.TLabel').pack(fill='x')
        body = ttk.Frame(self, padding=18)
        body.pack(fill='both', expand=True)
        tabs = ttk.Notebook(body)
        tabs.pack(fill='both', expand=True)
        data, options = ttk.Frame(tabs, padding=16), ttk.Frame(tabs, padding=16)
        tabs.add(data, text='Variáveis', image=parent.icons['table'], compound='left')
        tabs.add(options, text='Escalas e títulos', image=parent.icons['options'], compound='left')
        labels = [f'C{i + 1}  {name}' for i, name in enumerate(parent.headers)]
        self.y = self.combo(data, 0, 'Variável Y:', labels)
        self.y.current(max(0, parent.column.current()))
        self.x = None
        if kind == 'scatter':
            self.x = self.combo(data, 1, 'Variável X:', labels)
            self.x.current(1 if len(labels) > 1 and self.y.current() != 1 else 0)
        self.group = self.combo(data, 2, 'Por grupo (opcional):', ['Sem grupo'] + labels)
        self.group.current(0)
        self.connect = tk.BooleanVar(self, value=kind == 'time')
        self.connect_missing = tk.BooleanVar(self, value=False)
        self.connection_check = ttk.Checkbutton(data, text='Conectar pontos na ordem da planilha', variable=self.connect,
                                               command=self.toggle_connections)
        self.connection_check.grid(row=3, column=0, columnspan=2, sticky='w', pady=(16, 4))
        if kind == 'time':
            self.connection_check.state(['disabled'])
        self.missing_check = ttk.Checkbutton(data, text='Conectar através de valores ausentes', variable=self.connect_missing)
        self.missing_check.grid(row=4, column=0, columnspan=2, sticky='w', pady=4)
        ttk.Label(data, text=('O eixo X usa os números originais das linhas, incluindo lacunas.' if kind == 'time' else
                             'Linhas com X, Y ou grupo ausente são omitidas.'), wraplength=440).grid(row=5, column=0, columnspan=2, sticky='w', pady=(14, 0))
        self.x_log, self.y_log = tk.BooleanVar(self), tk.BooleanVar(self)
        ttk.Checkbutton(options, text='Escala logarítmica de X', variable=self.x_log).grid(row=0, column=0, columnspan=2, sticky='w', pady=4)
        ttk.Checkbutton(options, text='Escala logarítmica de Y', variable=self.y_log).grid(row=1, column=0, columnspan=2, sticky='w', pady=4)
        self.title_value = self.entry(options, 2, 'Título (opcional):')
        self.x_label = self.entry(options, 3, 'Título de X (opcional):')
        self.y_label = self.entry(options, 4, 'Título de Y (opcional):')
        actions = ttk.Frame(body)
        actions.pack(fill='x', pady=(16, 0))
        ttk.Button(actions, text='Cancelar', command=self.destroy).pack(side='right', padx=(8, 0))
        ttk.Button(actions, text='Criar gráfico', style='Accent.TButton', command=self.submit).pack(side='right')
        self.bind('<Escape>', lambda e: self.destroy())
        self.bind('<Return>', lambda e: self.submit())
        self.toggle_connections()
        parent.center_dialog(self)
        self.grab_set()
        self.y.focus_set()

    @staticmethod
    def combo(frame, row, label, values):
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky='w', padx=(0, 16), pady=8)
        widget = ttk.Combobox(frame, state='readonly', values=values, width=34)
        widget.grid(row=row, column=1, sticky='w')
        return widget

    @staticmethod
    def entry(frame, row, label):
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky='w', padx=(0, 16), pady=8)
        widget = ttk.Entry(frame, width=34)
        widget.grid(row=row, column=1, sticky='w')
        return widget

    def toggle_connections(self):
        self.missing_check.state(['!disabled'] if self.connect.get() else ['disabled'])

    def submit(self):
        graph = self.parent.run_xy_graph(self.kind, self.y.current(), self.x.current() if self.x else None,
                                        group=self.group.current() - 1 if self.group.current() > 0 else None,
                                        connect=self.connect.get(), connect_missing=self.connect_missing.get(),
                                        x_log=self.x_log.get(), y_log=self.y_log.get(),
                                        title=self.title_value.get(), x_label=self.x_label.get(), y_label=self.y_label.get())
        if graph is not None:
            self.destroy()
