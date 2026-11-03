import tkinter as tk
from tkinter import ttk, messagebox

from basic_inference import parse_count
from poisson_inference import METHODS, TITLE


class PoissonDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title(TITLE)
        self.transient(parent)
        self.resizable(False, False)
        body = ttk.Frame(self, padding=18)
        body.pack(fill='both', expand=True)
        ttk.Label(body, text=TITLE, style='Title.TLabel').pack(anchor='w', pady=(0, 12))
        self.tabs = ttk.Notebook(body)
        self.tabs.pack(fill='both', expand=True)
        data, options = ttk.Frame(self.tabs, padding=14), ttk.Frame(self.tabs, padding=14)
        self.tabs.add(data, text='Dados', image=parent.icons['table'], compound='left')
        self.tabs.add(options, text='Opções', image=parent.icons['options'], compound='left')
        ttk.Label(data, text='Formato:').grid(row=0, column=0, sticky='w')
        self.source = ttk.Combobox(data, state='readonly', values=['Contagens em uma coluna', 'Dados resumidos'], width=33)
        self.source.current(0)
        self.source.grid(row=0, column=1, sticky='w', pady=7)
        self.source.bind('<<ComboboxSelected>>', lambda e: self.toggle_source())
        self.column_frame, self.summary_frame = ttk.Frame(data), ttk.Frame(data)
        self.column_frame.grid(row=1, column=0, columnspan=2, sticky='w')
        self.summary_frame.grid(row=1, column=0, columnspan=2, sticky='w')
        ttk.Label(self.column_frame, text='Contagens:').grid(row=0, column=0, padx=(0, 15))
        self.column = ttk.Combobox(self.column_frame, state='readonly', width=33,
                                  values=[f'C{i+1}  {h}' for i, h in enumerate(parent.headers)])
        self.column.current(min(parent.worksheet.active[1], len(parent.headers)-1))
        self.column.grid(row=0, column=1, pady=7)
        self.events = self.entry(self.summary_frame, 0, 'Total de ocorrências:', '0')
        self.n = self.entry(self.summary_frame, 1, 'Número de observações:', '10')
        self.length = self.entry(data, 2, 'Exposição por observação:', '1')
        ttk.Label(options, text='Método:').grid(row=0, column=0, sticky='w')
        self.method = ttk.Combobox(options, state='readonly', width=48, values=list(METHODS.values()))
        self.method.current(0)
        self.method.grid(row=0, column=1, pady=7)
        self.confidence = self.entry(options, 1, 'Confiança (%):', '95')
        self.perform_test = tk.BooleanVar(self, value=True)
        ttk.Checkbutton(options, text='Realizar teste de hipótese', variable=self.perform_test,
                        command=self.toggle_test).grid(row=2, column=0, columnspan=2, sticky='w', pady=7)
        self.null = self.entry(options, 3, 'Taxa hipotética por unidade:', '1')
        ttk.Label(options, text='Alternativa / direção do IC:').grid(row=4, column=0, sticky='w')
        self.alternative = ttk.Combobox(options, state='readonly', width=28,
                                       values=['Diferente de (≠)', 'Menor que (<)', 'Maior que (>)'])
        self.alternative.current(0)
        self.alternative.grid(row=4, column=1, sticky='w', pady=7)
        ttk.Label(body, text='Use contagens inteiras não negativas. A exposição deve ser a mesma em cada observação.\n'
                  'A taxa e a hipótese são expressas por unidade de tempo, área ou outra exposição.',
                  wraplength=570, foreground='#536477').pack(fill='x', pady=12)
        actions = ttk.Frame(body)
        actions.pack(fill='x')
        ttk.Button(actions, text='Cancelar', command=self.destroy).pack(side='right', padx=(8, 0))
        ttk.Button(actions, text='Calcular', command=self.submit, style='Accent.TButton').pack(side='right')
        self.bind('<Escape>', lambda e: self.destroy())
        self.bind('<Return>', lambda e: self.submit())
        self.toggle_source()
        parent.center_dialog(self)
        self.grab_set()

    @staticmethod
    def entry(frame, row, label, value):
        ttk.Label(frame, text=label).grid(row=row, column=0, sticky='w', padx=(0, 15), pady=7)
        entry = ttk.Entry(frame, width=24)
        entry.insert(0, value)
        entry.grid(row=row, column=1, sticky='w', pady=7)
        return entry

    def toggle_source(self):
        self.column_frame.grid() if self.source.current() == 0 else self.column_frame.grid_remove()
        self.summary_frame.grid_remove() if self.source.current() == 0 else self.summary_frame.grid()

    def toggle_test(self):
        self.null.configure(state='normal' if self.perform_test.get() else 'disabled')

    def submit(self):
        try:
            number = lambda entry: float(entry.get().strip().replace(',', '.'))
            options = dict(length=number(self.length), confidence=number(self.confidence),
                           null=number(self.null) if self.perform_test.get() else 0.,
                           alternative=('two-sided', 'less', 'greater')[self.alternative.current()],
                           method=list(METHODS)[self.method.current()])
            source = 'column' if self.source.current() == 0 else 'summary'
            if source == 'column':
                options['column'] = self.column.current()
            else:
                options.update(events=parse_count(self.events.get(), 'Total de ocorrências'),
                               n=parse_count(self.n.get(), 'Número de observações', 1))
            if self.parent.run_poisson(source, perform_test=self.perform_test.get(), **options):
                self.destroy()
        except (ValueError, ArithmeticError) as error:
            messagebox.showerror('Dados inválidos', str(error), parent=self)
