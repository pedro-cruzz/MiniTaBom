import math
import tkinter as tk
from tkinter import ttk, messagebox

from basic_inference import parse_count
from extended_inference import EXTENDED_TITLES


class ExtendedInferenceDialog(tk.Toplevel):
    def __init__(self, parent, mode):
        super().__init__(parent)
        self.parent, self.mode = parent, mode
        self.proportion = mode == 'two_proportions'
        self.count = 1 if mode == 'one_variance' else 2
        self.title(EXTENDED_TITLES[mode])
        self.transient(parent)
        self.resizable(False, False)
        ttk.Label(self, text=EXTENDED_TITLES[mode], style='Title.TLabel').pack(fill='x')
        body = ttk.Frame(self, padding=16)
        body.pack(fill='both', expand=True)
        self.tabs = ttk.Notebook(body)
        self.tabs.pack(fill='both', expand=True)
        data, options = ttk.Frame(self.tabs, padding=16), ttk.Frame(self.tabs, padding=16)
        self.tabs.add(data, text='Dados', image=parent.icons['table'], compound='left')
        self.tabs.add(options, text='Opções', image=parent.icons['options'], compound='left')
        self.source_keys = ['columns', 'summary'] if self.count == 1 else ['columns', 'stacked', 'summary']
        self.source = ttk.Combobox(data, state='readonly', width=48, values=(
            ['Amostra em uma coluna', 'Dados resumidos'] if self.count == 1 else
            ['Amostras em colunas separadas', 'Amostras empilhadas com coluna de grupo', 'Dados resumidos']))
        self.source.current(0)
        self.source.grid(row=0, column=0, sticky='ew', pady=(0, 12))
        self.source.bind('<<ComboboxSelected>>', lambda e: self.toggle_source())
        self.frames = {key: ttk.Frame(data) for key in self.source_keys}
        for frame in self.frames.values():
            frame.grid(row=1, column=0, sticky='ew')
        self.columns, self.events = [], []
        for i in range(self.count):
            self.columns.append(self.column_picker(self.frames['columns'], i * 2, f'Amostra {i + 1}:', i))
            if self.proportion:
                self.events.append(self.entry(self.frames['columns'], i * 2 + 1, f'Evento da amostra {i + 1}:', 'Sim'))
        if self.count == 2:
            self.stacked_column = self.column_picker(self.frames['stacked'], 0, 'Amostras:', 0)
            self.group = self.column_picker(self.frames['stacked'], 1, 'Grupos:', 1)
            if self.proportion:
                self.stacked_event = self.entry(self.frames['stacked'], 2, 'Evento nos dois grupos:', 'Sim')
            ttk.Label(self.frames['stacked'], text='Amostra 1 = primeiro grupo observado; amostra 2 = segundo.\n'
                      'Linhas com grupo ausente são excluídas.', foreground='#536477').grid(
                          row=3, column=0, columnspan=2, sticky='w', pady=(10, 0))
        self.ns, self.values, self.value_labels = [], [], []
        for i in range(self.count):
            self.ns.append(self.entry(self.frames['summary'], i * 2, f'N da amostra {i + 1}:'))
            label = ttk.Label(self.frames['summary'], text=f'Eventos da amostra {i + 1}:')
            label.grid(row=i * 2 + 1, column=0, sticky='w', padx=(0, 16), pady=7)
            value = ttk.Entry(self.frames['summary'], width=25)
            value.grid(row=i * 2 + 1, column=1, sticky='w')
            self.values.append(value)
            self.value_labels.append(label)
        self.perform_test = tk.BooleanVar(self, value=True)
        ttk.Checkbutton(options, text='Realizar teste de hipótese', variable=self.perform_test,
                        command=self.toggle_test).grid(row=0, column=0, columnspan=2, sticky='w', pady=7)
        self.null_label = ttk.Label(options, text='Diferença hipotética (p1−p2):' if self.proportion else '')
        self.null_label.grid(row=1, column=0, sticky='w', padx=(0, 16), pady=7)
        self.null = ttk.Entry(options, width=25)
        self.null.insert(0, '0' if self.proportion else '1')
        self.null.grid(row=1, column=1, sticky='w')
        self.confidence = self.entry(options, 2, 'Nível de confiança (%):', '95')
        ttk.Label(options, text='Hipótese alternativa:').grid(row=3, column=0, sticky='w', padx=(0, 16), pady=7)
        self.alternative = ttk.Combobox(options, state='readonly', width=29,
                                       values=['Diferente de (≠)', 'Menor que (<)', 'Maior que (>)'])
        self.alternative.current(0)
        self.alternative.grid(row=3, column=1, sticky='w')
        if self.proportion:
            self.pooled = tk.BooleanVar(self, value=False)
            self.pooled_control = ttk.Checkbutton(options, text='Usar estimativa combinada no teste Z (exige diferença 0)',
                                                 variable=self.pooled)
            self.pooled_control.grid(row=4, column=0, columnspan=2, sticky='w', pady=10)
            note = ('IC Wald com estimativas separadas. Fisher é calculado para diferença hipotética zero.\n'
                    'Eventos são textos exatos; vazio e * são ausentes.')
        else:
            ttk.Label(options, text='Medida informada:').grid(row=4, column=0, sticky='w', pady=7)
            self.measure = ttk.Combobox(options, state='readonly', width=29, values=['Desvio padrão', 'Variância'])
            self.measure.current(0)
            self.measure.grid(row=4, column=1, sticky='w')
            self.measure.bind('<<ComboboxSelected>>', lambda e: self.update_measure())
            self.update_measure()
            note = ('Método qui-quadrado (uma amostra) ou F (duas amostras).\n'
                    'Estes métodos pressupõem populações normais e observações independentes.')
        ttk.Label(body, text=note, wraplength=540, foreground='#536477').pack(fill='x', pady=(12, 0))
        actions = ttk.Frame(body)
        actions.pack(fill='x', pady=(16, 0))
        ttk.Button(actions, text='Cancelar', command=self.destroy).pack(side='right', padx=(8, 0))
        ttk.Button(actions, text='Calcular', style='Accent.TButton', command=self.submit).pack(side='right')
        self.bind('<Escape>', lambda e: self.destroy())
        self.bind('<Return>', lambda e: self.submit())
        self.toggle_source()
        parent.center_dialog(self)
        self.grab_set()

    @staticmethod
    def entry(frame, row, label, initial=''):
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky='w', padx=(0, 16), pady=7)
        entry = ttk.Entry(frame, width=25)
        entry.insert(0, initial)
        entry.grid(row=row, column=1, sticky='w')
        return entry

    def column_picker(self, frame, row, label, default):
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky='w', padx=(0, 16), pady=7)
        picker = ttk.Combobox(frame, state='readonly', width=31,
                              values=[f'C{i + 1}  {name}' for i, name in enumerate(self.parent.headers)])
        picker.current(min(default, len(self.parent.headers) - 1))
        picker.grid(row=row, column=1, sticky='w')
        return picker

    def toggle_source(self):
        source = self.source_keys[self.source.current()]
        for key, frame in self.frames.items():
            frame.grid() if key == source else frame.grid_remove()

    def toggle_test(self):
        self.null.configure(state='normal' if self.perform_test.get() else 'disabled')
        if self.proportion:
            self.pooled_control.configure(state='normal' if self.perform_test.get() else 'disabled')

    def update_measure(self):
        parameter = 'Desvio padrão' if self.measure.current() == 0 else 'Variância'
        self.null_label.configure(text=parameter + (' hipotético:' if self.measure.current() == 0 else ' hipotética:') if self.count == 1 else
                                  ('Razão hipotética (σ1/σ2):' if self.measure.current() == 0 else 'Razão hipotética (σ1²/σ2²):'))
        for i, label in enumerate(self.value_labels, 1):
            label.configure(text=f'{"Desvio" if self.measure.current() == 0 else "Variância"} da amostra {i}:')

    @staticmethod
    def number(entry):
        value = float(entry.get().strip().replace(',', '.'))
        if not math.isfinite(value):
            raise ValueError('Use apenas números finitos.')
        return value

    def submit(self):
        source = self.source_keys[self.source.current()]
        try:
            options = dict(confidence=self.number(self.confidence),
                           null=self.number(self.null) if self.perform_test.get() else (0 if self.proportion else 1),
                           alternative=('two-sided', 'less', 'greater')[self.alternative.current()])
            if self.proportion:
                options['pooled'] = self.pooled.get() if self.perform_test.get() else False
            else:
                options['measure'] = 'sd' if self.measure.current() == 0 else 'variance'
            if source == 'summary':
                for i, (n, value) in enumerate(zip(self.ns, self.values), 1):
                    suffix = str(i) if self.count == 2 else ''
                    options['n' + suffix] = parse_count(n.get(), 'N', 1 if self.proportion else 2)
                    options[('events' if self.proportion else 'value') + suffix] = (
                        parse_count(value.get(), 'Eventos') if self.proportion else self.number(value))
            else:
                options['columns'] = ([picker.current() for picker in self.columns] if source == 'columns'
                                      else [self.stacked_column.current()])
                if source == 'stacked':
                    options['group'] = self.group.current()
                if self.proportion:
                    options['events'] = ([entry.get() for entry in self.events] if source == 'columns' else
                                         [self.stacked_event.get()] * 2)
        except ValueError as error:
            messagebox.showerror('Dados inválidos', str(error), parent=self)
            return
        if self.parent.run_extended_test(self.mode, source, perform_test=self.perform_test.get(), **options):
            self.destroy()
