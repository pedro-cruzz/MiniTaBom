import math
import tkinter as tk
from tkinter import ttk, messagebox

from basic_inference import PROPORTION_METHODS, parse_count


BASIC_TITLES = {'z': 'Teste Z de uma amostra', 'proportion': 'Teste de uma proporção'}


class BasicInferenceDialog(tk.Toplevel):
    def __init__(self, parent, mode):
        super().__init__(parent)
        self.parent, self.mode = parent, mode
        self.title(BASIC_TITLES[mode])
        self.transient(parent)
        self.resizable(False, False)
        ttk.Label(self, text=BASIC_TITLES[mode], style='Title.TLabel').pack(fill='x')
        body = ttk.Frame(self, padding=18)
        body.pack(fill='both', expand=True)
        tabs = ttk.Notebook(body)
        tabs.pack(fill='both', expand=True)
        data, options = ttk.Frame(tabs, padding=16), ttk.Frame(tabs, padding=16)
        tabs.add(data, text='Dados', image=parent.icons['table'], compound='left')
        tabs.add(options, text='Opções', image=parent.icons['options'], compound='left')
        self.source = ttk.Combobox(data, state='readonly', width=46,
                                  values=['Amostra em uma coluna', 'Dados resumidos'])
        self.source.current(0)
        self.source.grid(row=0, column=0, columnspan=2, sticky='ew', pady=(0, 12))
        self.source.bind('<<ComboboxSelected>>', lambda e: self.toggle_source())
        self.column_frame = ttk.Frame(data)
        self.column_frame.grid(row=1, column=0, columnspan=2, sticky='ew')
        ttk.Label(self.column_frame, text='Amostra:').grid(row=0, column=0, sticky='w', padx=(0, 16), pady=6)
        self.column = ttk.Combobox(self.column_frame, state='readonly', width=34,
                                  values=[f'C{i + 1}  {name}' for i, name in enumerate(parent.headers)])
        self.column.current(max(0, parent.column.current()))
        self.column.grid(row=0, column=1, sticky='w')
        self.event = None
        if mode == 'proportion':
            ttk.Label(self.column_frame, text='Evento:').grid(row=1, column=0, sticky='w', pady=6)
            self.event = ttk.Combobox(self.column_frame, width=34)
            self.event.grid(row=1, column=1, sticky='w')
            self.column.bind('<<ComboboxSelected>>', lambda e: self.update_events())
            self.update_events()
        self.summary_frame = ttk.Frame(data)
        self.summary_frame.grid(row=1, column=0, columnspan=2, sticky='ew')
        self.n = self.add_entry(self.summary_frame, 0, 'Tamanho amostral:' if mode == 'z' else 'Número de ensaios:')
        self.value = self.add_entry(self.summary_frame, 1, 'Média amostral:' if mode == 'z' else 'Número de eventos:')
        self.sigma = self.add_entry(data, 2, 'Desvio padrão conhecido:') if mode == 'z' else None
        info = ('Informe o sigma populacional conhecido. Ausentes na coluna são omitidos.' if mode == 'z' else
                'A coluna aceita até duas categorias. Vazio e * são ausentes. O evento distingue maiúsculas e minúsculas.')
        ttk.Label(data, text=info, wraplength=440, foreground='#536477').grid(row=3, column=0, columnspan=2, sticky='w', pady=(14, 4))
        self.perform_test = tk.BooleanVar(self, value=True)
        ttk.Checkbutton(options, text='Realizar teste de hipótese', variable=self.perform_test,
                        command=self.toggle_test).grid(row=0, column=0, columnspan=2, sticky='w', pady=8)
        self.null = self.add_entry(options, 1, 'Média hipotética:' if mode == 'z' else 'Proporção hipotética:', '0' if mode == 'z' else '0,5')
        self.confidence = self.add_entry(options, 2, 'Nível de confiança (%):', '95')
        ttk.Label(options, text='Hipótese alternativa:').grid(row=3, column=0, sticky='w', padx=(0, 16), pady=8)
        self.alternative = ttk.Combobox(options, state='readonly', width=27,
                                       values=['Diferente de (≠)', 'Menor que (<)', 'Maior que (>)'])
        self.alternative.current(0)
        self.alternative.grid(row=3, column=1, sticky='w')
        self.method = None
        if mode == 'proportion':
            ttk.Label(options, text='Método:').grid(row=4, column=0, sticky='w', pady=8)
            self.method = ttk.Combobox(options, state='readonly', width=43, values=list(PROPORTION_METHODS.values()))
            self.method.current(0)
            self.method.grid(row=4, column=1, sticky='w')
        actions = ttk.Frame(body)
        actions.pack(fill='x', pady=(16, 0))
        ttk.Button(actions, text='Cancelar', command=self.destroy).pack(side='right', padx=(8, 0))
        ttk.Button(actions, text='Calcular', style='Accent.TButton', command=self.submit).pack(side='right')
        self.bind('<Escape>', lambda e: self.destroy())
        self.bind('<Return>', lambda e: self.submit())
        self.toggle_source()
        parent.center_dialog(self)
        self.grab_set()
        self.column.focus_set()

    @staticmethod
    def add_entry(frame, row, label, value=''):
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky='w', padx=(0, 16), pady=8)
        entry = ttk.Entry(frame, width=20)
        entry.insert(0, value)
        entry.grid(row=row, column=1, sticky='w')
        return entry

    def toggle_source(self):
        self.column_frame.grid() if self.source.current() == 0 else self.column_frame.grid_remove()
        self.summary_frame.grid_remove() if self.source.current() == 0 else self.summary_frame.grid()

    def toggle_test(self):
        self.null.configure(state='normal' if self.perform_test.get() else 'disabled')

    def update_events(self):
        values = list(dict.fromkeys(str(row[self.column.current()]).strip() for row in self.parent.rows
                                   if str(row[self.column.current()]).strip() not in ('', '*')))
        self.event.configure(values=values[:100])
        self.event.set(values[0] if values else '')

    def submit(self):
        try:
            confidence = float(self.confidence.get().strip().replace(',', '.'))
            null = float(self.null.get().strip().replace(',', '.')) if self.perform_test.get() else (0 if self.mode == 'z' else .5)
            if not all(math.isfinite(v) for v in (confidence, null)):
                raise ValueError('Use opções numéricas finitas.')
            options = dict(confidence=confidence, null=null,
                           alternative=('two-sided', 'less', 'greater')[self.alternative.current()])
            if self.mode == 'z':
                options['sigma'] = float(self.sigma.get().strip().replace(',', '.'))
            else:
                options['method'] = list(PROPORTION_METHODS)[self.method.current()]
            if self.source.current() == 1:
                options['n'] = parse_count(self.n.get(), 'Tamanho amostral', 2 if self.mode == 'z' else 1)
                options['mean' if self.mode == 'z' else 'events'] = (
                    float(self.value.get().strip().replace(',', '.')) if self.mode == 'z' else
                    parse_count(self.value.get(), 'Número de eventos'))
        except ValueError as error:
            messagebox.showerror('Dados inválidos', str(error), parent=self)
            return
        if self.parent.run_basic_test(self.mode, 'column' if self.source.current() == 0 else 'summary',
                column=self.column.current(), event=self.event.get() if self.event else None,
                perform_test=self.perform_test.get(), **options):
            self.destroy()
