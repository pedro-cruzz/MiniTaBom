import math
import tkinter as tk
from tkinter import ttk, messagebox
from basic_inference import parse_count


TITLES = {'one': 'Teste t de uma amostra', 'paired': 'Teste t pareado', 'two': 'Teste t de duas amostras'}


class InferenceDialog(tk.Toplevel):
    def __init__(self, parent, mode):
        super().__init__(parent)
        self.parent, self.mode = parent, mode
        self.title(TITLES[mode])
        self.transient(parent)
        self.resizable(False, False)
        ttk.Label(self, text=TITLES[mode], style='Title.TLabel').pack(fill='x')
        body = ttk.Frame(self, padding=20)
        body.pack(fill='both', expand=True)
        notebook = ttk.Notebook(body)
        notebook.pack(fill='both', expand=True)
        data = ttk.Frame(notebook, padding=16)
        options = ttk.Frame(notebook, padding=16)
        notebook.add(data, text='Dados', image=parent.icons['table'], compound='left')
        notebook.add(options, text='Opções', image=parent.icons['options'], compound='left')
        self.source = ttk.Combobox(data, state='readonly', width=48,
            values=(['Amostras em colunas separadas', 'Dados resumidos', 'Resposta e grupo em duas colunas']
                    if mode == 'two' else ['Dados em coluna(s)', 'Dados resumidos das diferenças' if mode == 'paired' else 'Dados resumidos']))
        self.source.current(0)
        self.source.grid(row=0, column=0, columnspan=2, sticky='ew', pady=(0, 10))
        self.source.bind('<<ComboboxSelected>>', lambda e: self.toggle_source())
        self.column_frame = ttk.Frame(data)
        self.column_frame.grid(row=1, column=0, columnspan=2, sticky='ew')
        labels = [f'C{i + 1}  {name}' for i, name in enumerate(parent.headers)]
        self.first_label = ttk.Label(self.column_frame, text='Amostra:' if mode == 'one' else 'Primeira amostra:')
        self.first_label.grid(row=0, column=0, sticky='w', pady=8, padx=(0, 16))
        self.first = ttk.Combobox(self.column_frame, values=labels, state='readonly', width=36)
        self.first.grid(row=0, column=1, sticky='ew')
        self.first.current(parent.column.current())
        self.second = None
        if mode != 'one':
            self.second_label = ttk.Label(self.column_frame, text='Segunda amostra:')
            self.second_label.grid(row=1, column=0, sticky='w', pady=8)
            self.second = ttk.Combobox(self.column_frame, values=labels, state='readonly', width=36)
            self.second.grid(row=1, column=1, sticky='ew')
            if len(labels) > 1:
                self.second.current(1 if self.first.current() != 1 else 0)
        self.summary_frame = ttk.Frame(data)
        self.summary_frame.grid(row=1, column=0, columnspan=2, sticky='ew')
        self.summary_entries = []
        for sample_index in range(2 if mode == 'two' else 1):
            frame = ttk.LabelFrame(self.summary_frame,
                text=f'Amostra {sample_index + 1}' if mode == 'two' else 'Diferenças: primeira − segunda' if mode == 'paired' else 'Amostra', padding=8)
            frame.grid(row=0, column=sample_index, sticky='nsew', padx=4)
            entries = {}
            for row, (key, text) in enumerate([('n', 'Tamanho amostral:'), ('mean', 'Média:'), ('sd', 'Desvio padrão amostral:')]):
                ttk.Label(frame, text=text).grid(row=row, column=0, sticky='w', pady=4)
                entry = ttk.Entry(frame, width=15)
                entry.grid(row=row, column=1, padx=6)
                entries[key] = entry
            self.summary_entries.append(entries)
        self.info = ttk.Label(data, wraplength=490, foreground='#62758a')
        self.info.grid(row=2, column=0, columnspan=2, sticky='w', pady=(12, 8))
        if mode != 'one':
            ttk.Label(data, text='Diferença = primeira amostra − segunda amostra.', wraplength=490).grid(row=3, column=0, columnspan=2, sticky='w')
        self.perform_test = tk.BooleanVar(self, value=True)
        ttk.Checkbutton(data, text='Realizar teste de hipótese', variable=self.perform_test, command=self.toggle_test).grid(row=4, column=0, columnspan=2, sticky='w', pady=(20, 8))
        ttk.Label(data, text='Média hipotética:' if mode == 'one' else 'Diferença hipotética:').grid(row=5, column=0, sticky='w')
        self.null = ttk.Entry(data, width=16)
        self.null.insert(0, '0')
        self.null.grid(row=5, column=1, sticky='w')
        ttk.Label(options, text='Nível de confiança (%):').grid(row=0, column=0, sticky='w', padx=(0, 16), pady=10)
        self.confidence = ttk.Entry(options, width=16)
        self.confidence.insert(0, '95')
        self.confidence.grid(row=0, column=1, sticky='w')
        ttk.Label(options, text='Hipótese alternativa:').grid(row=1, column=0, sticky='w', pady=10)
        self.alternative = ttk.Combobox(options, state='readonly', width=25,
            values=['Diferente de (≠)', 'Menor que (<)', 'Maior que (>)'])
        self.alternative.current(0)
        self.alternative.grid(row=1, column=1, sticky='w')
        self.equal_var = tk.BooleanVar(self, value=False)
        self.legacy_df = tk.BooleanVar(self, value=True)
        self.store = tk.BooleanVar(self,value=False)
        if mode=='paired':
            ttk.Checkbutton(options,text='Armazenar diferenças na planilha (dados em colunas)',variable=self.store).grid(row=3,column=0,columnspan=2,sticky='w',pady=10)
        if mode == 'two':
            ttk.Separator(options).grid(row=2, column=0, columnspan=2, sticky='ew', pady=12)
            ttk.Checkbutton(options, text='Assumir variâncias iguais', variable=self.equal_var).grid(row=3, column=0, columnspan=2, sticky='w', pady=4)
            ttk.Checkbutton(options, text='Welch: truncar GL para inteiro (referência Minitab 16)', variable=self.legacy_df).grid(row=4, column=0, columnspan=2, sticky='w', pady=4)
        actions = ttk.Frame(body)
        actions.pack(fill='x', pady=(18, 0))
        ttk.Button(actions, text='Cancelar', command=self.destroy).pack(side='right', padx=(8, 0))
        ttk.Button(actions, text='Calcular', style='Accent.TButton', command=self.submit).pack(side='right')
        self.bind('<Escape>', lambda event: self.destroy())
        self.bind('<Return>', lambda event: self.submit())
        self.toggle_source()
        parent.center_dialog(self)
        self.grab_set()
        self.first.focus_set()

    def toggle_source(self):
        summary = self.source.current() == 1
        if summary and hasattr(self,'store'):
            self.store.set(False)
        self.column_frame.grid_remove() if summary else self.column_frame.grid()
        self.summary_frame.grid() if summary else self.summary_frame.grid_remove()
        if self.mode == 'two':
            stacked = self.source.current() == 2
            self.first_label.configure(text='Resposta:' if stacked else 'Primeira amostra:')
            self.second_label.configure(text='Grupo:' if stacked else 'Segunda amostra:')
        info = ('Informe o resumo das diferenças, e não os resumos separados das amostras.' if summary and self.mode == 'paired'
                else 'N ≥ 2. Informe desvio padrão amostral; não o erro padrão.' if summary
                else 'Ordem das amostras: primeira aparição dos dois grupos. Grupo ausente exclui a linha.' if self.source.current() == 2
                else 'Cada linha é um par. Se faltar um valor, o par inteiro é omitido.' if self.mode == 'paired'
                else 'As observações ausentes são omitidas por amostra.')
        self.info.configure(text=info)
        self.parent.center_dialog(self)

    def toggle_test(self):
        self.null.configure(state='normal' if self.perform_test.get() else 'disabled')

    def submit(self):
        try:
            confidence = float(self.confidence.get().strip().replace(',', '.'))
            null = float(self.null.get().strip().replace(',', '.')) if self.perform_test.get() else 0
            if not all(math.isfinite(v) for v in (confidence, null)):
                raise ValueError('Use valores numéricos finitos nas opções.')
            summaries = None
            if self.source.current() == 1:
                summaries = [dict(n=parse_count(entries['n'].get(), 'Tamanho amostral', 2),
                                  mean=float(entries['mean'].get().strip().replace(',', '.')),
                                  sd=float(entries['sd'].get().strip().replace(',', '.')))
                             for entries in self.summary_entries]
        except ValueError as error:
            messagebox.showerror('Dados ou opções inválidos', 'Confira os resumos e as opções informados.\n' + str(error), parent=self)
            return
        if self.parent.run_ttest(self.mode, self.first.current(),
                self.second.current() if self.second is not None else None,
                source=('columns', 'summary', 'stacked')[self.source.current()], summaries=summaries,
                null=null, confidence=confidence,
                alternative=('two-sided', 'less', 'greater')[self.alternative.current()],
                equal_var=self.equal_var.get(), legacy_df=self.legacy_df.get(),
                perform_test=self.perform_test.get(),store=self.store.get()):
            self.destroy()
