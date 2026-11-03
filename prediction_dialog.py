import math
import tkinter as tk
from tkinter import ttk, messagebox


class PredictionDialog(tk.Toplevel):
    def __init__(self, parent, model):
        super().__init__(parent)
        self.app = parent
        self.title('Prever resposta — ' + model['response'])
        self.transient(parent)
        self.resizable(False, False)
        body = ttk.Frame(self, padding=12)
        body.pack(fill='both', expand=True)
        ttk.Label(body, text='Resposta: ' + model['response'] + f"    •    N do ajuste: {model['n']}", style='Title.TLabel').pack(fill='x', pady=(0, 8))
        self.tabs = ttk.Notebook(body)
        self.tabs.pack(fill='both', expand=True)
        manual = ttk.Frame(self.tabs, padding=12)
        columns = ttk.Frame(self.tabs, padding=12)
        options = ttk.Frame(self.tabs, padding=12)
        self.tabs.add(manual, text='Digitar casos', image=parent.icons['predict'], compound='left')
        self.tabs.add(columns, text='Colunas da planilha', image=parent.icons['table'], compound='left')
        self.tabs.add(options, text='Intervalos', image=parent.icons['distribution'], compound='left')
        self.input_mode = 'text'
        self.tabs.bind('<<NotebookTabChanged>>', self.remember_mode)
        ttk.Label(manual, text='Um caso por linha; separe preditores com tabulação ou ponto e vírgula.\nAceita vírgula decimal.', wraplength=540).pack(anchor='w')
        ttk.Label(manual, text='Ordem: ' + '; '.join(model['predictors']), wraplength=540, font=('Segoe UI', 9, 'bold')).pack(anchor='w', pady=(8, 5))
        self.values = tk.Text(manual, width=66, height=9, wrap='none', font=('Consolas', 10), undo=True)
        scroll = ttk.Scrollbar(manual, orient='horizontal', command=self.values.xview)
        self.values.configure(xscrollcommand=scroll.set)
        self.values.pack(fill='both', expand=True)
        scroll.pack(fill='x')
        mapping = ttk.Frame(columns)
        mapping.pack(fill='both', expand=True)
        # Rolagem permite mapear modelos com muitos preditores sem ampliar a janela.
        canvas = tk.Canvas(mapping, width=535, height=205, highlightthickness=0, background='#f0f1f3')
        sy = ttk.Scrollbar(mapping, orient='vertical', command=canvas.yview)
        fields = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=fields, anchor='nw')
        fields.bind('<Configure>', lambda event: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.configure(yscrollcommand=sy.set)
        sy.pack(side='right', fill='y')
        canvas.pack(fill='both', expand=True)
        labels = [f'C{i + 1}  {label}' for i, label in enumerate(parent.headers)]
        self.columns = []
        for index, label in enumerate(model['predictors']):
            ttk.Label(fields, text=label, wraplength=220).grid(row=index, column=0, sticky='w', pady=5, padx=(0, 12))
            field = ttk.Combobox(fields, values=labels, state='readonly', width=32)
            field.grid(row=index, column=1, sticky='w', pady=5)
            if label in parent.headers:
                field.current(parent.headers.index(label))
            self.columns.append(field)
        self.omit_missing = tk.BooleanVar(value=True)
        ttk.Checkbutton(columns, text='Omitir linhas com algum preditor ausente', variable=self.omit_missing).pack(anchor='w', pady=(10, 0))
        ttk.Label(options, text='Confiança (%):').grid(row=0, column=0, sticky='w', padx=(0, 12), pady=10)
        self.confidence = ttk.Entry(options, width=12)
        self.confidence.insert(0, f"{model['confidence']:g}")
        self.confidence.grid(row=0, column=1, sticky='w')
        ttk.Label(options, text='Tipo de intervalo:').grid(row=1, column=0, sticky='w', pady=10)
        self.alternative = ttk.Combobox(options, state='readonly', values=['Bilateral', 'Limite inferior', 'Limite superior'], width=25)
        self.alternative.current(0)
        self.alternative.grid(row=1, column=1, sticky='w')
        ttk.Label(options, text='IC estima a média da resposta.\nIP estima uma única nova observação.\nOs dois intervalos serão apresentados.', justify='left').grid(row=2, column=0, columnspan=2, sticky='w', pady=15)
        actions = ttk.Frame(body)
        actions.pack(fill='x', pady=(12, 0))
        ttk.Button(actions, text='Cancelar', command=self.destroy).pack(side='right')
        ttk.Button(actions, text='Prever', command=self.submit).pack(side='right', padx=6)
        self.bind('<Escape>', lambda event: self.destroy())
        parent.center_dialog(self)
        self.grab_set()
        self.values.focus_set()

    def remember_mode(self, event=None):
        tab = self.tabs.index('current')
        if tab < 2:
            self.input_mode = 'text' if tab == 0 else 'columns'

    def submit(self):
        try:
            confidence = float(self.confidence.get().strip().replace(',', '.'))
            if not math.isfinite(confidence) or not 0 < confidence < 100:
                raise ValueError
        except ValueError:
            messagebox.showerror('Confiança inválida', 'Use confiança entre 0 e 100, sem os extremos.', parent=self)
            return
        kwargs = dict(confidence=confidence, alternative=('two-sided', 'lower', 'upper')[self.alternative.current()])
        if self.input_mode == 'text':
            kwargs['text'] = self.values.get('1.0', 'end-1c')
        else:
            kwargs.update(columns=[field.current() for field in self.columns], omit_missing=self.omit_missing.get())
        if self.app.run_prediction(**kwargs):
            self.destroy()
