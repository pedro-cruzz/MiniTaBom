"""Seleção comum de grupos para ANOVA e gráficos comparativos."""
import math
import tkinter as tk
from tkinter import ttk, messagebox


class GroupSelector(ttk.Frame):
    def __init__(self, parent, headers):
        super().__init__(parent)
        self.layout_mode = tk.StringVar(self, value='columns')
        self.headers = headers
        formats = ttk.Frame(self)
        formats.pack(fill='x', pady=(0, 12))
        ttk.Radiobutton(formats, text='Grupos em colunas separadas', variable=self.layout_mode,
                        value='columns', command=self.show_mode).pack(anchor='w', pady=3)
        ttk.Radiobutton(formats, text='Resposta em uma coluna e fator em outra', variable=self.layout_mode,
                        value='stacked', command=self.show_mode).pack(anchor='w', pady=3)
        self.columns_frame = ttk.Frame(self)
        ttk.Label(self.columns_frame, text='Selecione os grupos (Ctrl/clique ou Shift):').pack(anchor='w', pady=(0, 6))
        listing = ttk.Frame(self.columns_frame)
        listing.pack(fill='both', expand=True)
        self.columns = tk.Listbox(listing, selectmode='extended', exportselection=False,
                                  height=8, width=48, font=('Segoe UI', 10), relief='solid', borderwidth=1)
        sy = ttk.Scrollbar(listing, orient='vertical', command=self.columns.yview)
        self.columns.configure(yscrollcommand=sy.set)
        sy.pack(side='right', fill='y')
        self.columns.pack(fill='both', expand=True)
        controls = ttk.Frame(self.columns_frame)
        controls.pack(fill='x', pady=(8, 0))
        ttk.Button(controls, text='Selecionar todas', command=lambda: self.columns.selection_set(0, 'end')).pack(side='left')
        ttk.Button(controls, text='Limpar seleção', command=lambda: self.columns.selection_clear(0, 'end')).pack(side='left', padx=8)
        labels = [f'C{i + 1}  {name}' for i, name in enumerate(headers)]
        for label in labels:
            self.columns.insert('end', label)
        if len(labels) >= 2:
            self.columns.selection_set(0, 1)
        self.stacked_frame = ttk.Frame(self)
        ttk.Label(self.stacked_frame, text='Resposta numérica:').grid(row=0, column=0, sticky='w', padx=(0, 14), pady=8)
        ttk.Label(self.stacked_frame, text='Fator / grupo:').grid(row=1, column=0, sticky='w', pady=8)
        self.response = ttk.Combobox(self.stacked_frame, values=labels, state='readonly', width=30)
        self.factor = ttk.Combobox(self.stacked_frame, values=labels, state='readonly', width=30)
        self.response.grid(row=0, column=1)
        self.factor.grid(row=1, column=1)
        self.response.current(0)
        if len(labels) >= 2:
            self.factor.current(1)
        ttk.Label(self.stacked_frame, text='Cada linha associa uma medição ao seu grupo.\nFatores vazios ou * são omitidos.',
                  foreground='#62758a', wraplength=420).grid(row=2, column=0, columnspan=2, sticky='w', pady=16)
        self.show_mode()

    def show_mode(self):
        self.columns_frame.pack_forget()
        self.stacked_frame.pack_forget()
        frame = self.columns_frame if self.layout_mode.get() == 'columns' else self.stacked_frame
        frame.pack(fill='both', expand=True)

    def selection(self):
        if self.layout_mode.get() == 'columns':
            return dict(columns=list(self.columns.curselection()))
        return dict(response=self.response.current(), factor=self.factor.current())


class AnovaDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title('ANOVA de um fator')
        self.transient(parent)
        self.resizable(False, False)
        ttk.Label(self, text='ANOVA de um fator', style='Title.TLabel').pack(fill='x')
        body = ttk.Frame(self, padding=18)
        body.pack(fill='both', expand=True)
        notebook = ttk.Notebook(body)
        notebook.pack(fill='both', expand=True)
        data = ttk.Frame(notebook, padding=14)
        options = ttk.Frame(notebook, padding=14)
        notebook.add(data, text='Dados', image=parent.icons['table'], compound='left')
        notebook.add(options, text='Opções e comparações', image=parent.icons['options'], compound='left')
        self.selector = GroupSelector(data, parent.headers)
        self.selector.pack(fill='both', expand=True)
        self.equal_var = tk.BooleanVar(self, value=True)
        self.comparisons = tk.BooleanVar(self, value=False)
        self.show_graph = tk.BooleanVar(self, value=False)
        ttk.Checkbutton(options, text='Assumir variâncias iguais (ANOVA clássica)', variable=self.equal_var,
                        command=self.update_method).pack(anchor='w', pady=(6, 8))
        ttk.Label(options, text='Desmarcado: ANOVA de Welch.', foreground='#62758a').pack(anchor='w')
        confidence_row = ttk.Frame(options)
        confidence_row.pack(fill='x', pady=18)
        ttk.Label(confidence_row, text='Nível de confiança (%):').pack(side='left', padx=(0, 12))
        self.confidence = ttk.Entry(confidence_row, width=12)
        self.confidence.insert(0, '95')
        self.confidence.pack(side='left')
        ttk.Checkbutton(options, text='Comparar todos os pares de médias', variable=self.comparisons).pack(anchor='w', pady=6)
        self.method_label = ttk.Label(options, foreground='#62758a', wraplength=440)
        self.method_label.pack(anchor='w', pady=6)
        ttk.Checkbutton(options, text='Abrir boxplots dos grupos na mesma escala', variable=self.show_graph).pack(anchor='w', pady=12)
        self.update_method()
        actions = ttk.Frame(body)
        actions.pack(fill='x', pady=(16, 0))
        ttk.Button(actions, text='Cancelar', command=self.destroy).pack(side='right', padx=(8, 0))
        ttk.Button(actions, text='Calcular', style='Accent.TButton', command=self.submit).pack(side='right')
        self.bind('<Return>', lambda event: self.submit())
        self.bind('<Escape>', lambda event: self.destroy())
        parent.center_dialog(self)
        self.grab_set()

    def update_method(self):
        self.method_label.configure(text=('Tukey-Kramer: intervalos simultâneos e valores-p ajustados.'
                                          if self.equal_var.get() else
                                          'Games-Howell: comparações sem assumir variâncias iguais.'))

    def submit(self):
        try:
            confidence = float(self.confidence.get().strip().replace(',', '.'))
            if not math.isfinite(confidence):
                raise ValueError('Nível de confiança não finito.')
        except ValueError:
            messagebox.showerror('Opções inválidas', 'Informe um nível de confiança numérico entre 0 e 100.', parent=self)
            return
        if self.parent.run_anova(**self.selector.selection(), equal_var=self.equal_var.get(),
                confidence=confidence, comparisons=self.comparisons.get(), show_graph=self.show_graph.get()):
            self.destroy()


class GroupPlotDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title('Boxplots comparativos')
        self.transient(parent)
        self.resizable(False, False)
        ttk.Label(self, text='Boxplots comparativos', style='Title.TLabel').pack(fill='x')
        body = ttk.Frame(self, padding=18)
        body.pack(fill='both', expand=True)
        self.selector = GroupSelector(body, parent.headers)
        self.selector.pack(fill='both', expand=True)
        def submit():
            if parent.plot_groups(**self.selector.selection()):
                self.destroy()
        actions = ttk.Frame(body)
        actions.pack(fill='x', pady=(16, 0))
        ttk.Button(actions, text='Cancelar', command=self.destroy).pack(side='right', padx=(8, 0))
        ttk.Button(actions, text='Criar gráfico', style='Accent.TButton', command=submit).pack(side='right')
        self.bind('<Escape>', lambda event: self.destroy())
        self.bind('<Return>', lambda event: submit())
        parent.center_dialog(self)
        self.grab_set()
