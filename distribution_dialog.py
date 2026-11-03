import tkinter as tk
from tkinter import ttk, messagebox
from distributions import DISTRIBUTIONS, OPERATIONS


class DistributionDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.app = parent
        self.title('Distribuições de probabilidade')
        self.transient(parent)
        self.resizable(False, False)
        body = ttk.Frame(self, padding=16)
        body.pack(fill='both', expand=True)
        ttk.Label(body, text='Distribuição:').grid(row=0, column=0, sticky='w', pady=6)
        self.distribution = ttk.Combobox(body, values=list(DISTRIBUTIONS), state='readonly', width=37)
        self.distribution.current(0)
        self.distribution.grid(row=0, column=1, sticky='ew', padx=(12, 0))
        self.distribution.bind('<<ComboboxSelected>>', self.update_parameters)
        self.parameter_frame = ttk.LabelFrame(body, text='Parâmetros', padding=10)
        self.parameter_frame.grid(row=1, column=0, columnspan=2, sticky='ew', pady=10)
        self.parameters = {}
        self.update_parameters()
        ttk.Label(body, text='Calcular:').grid(row=2, column=0, sticky='w', pady=6)
        self.operation = ttk.Combobox(body, values=list(OPERATIONS.values()), state='readonly', width=37)
        self.operation.current(1)
        self.operation.grid(row=2, column=1, sticky='ew', padx=(12, 0))
        self.operation.bind('<<ComboboxSelected>>', self.update_inputs)
        self.input_label = ttk.Label(body, text='Valor x:')
        self.input_label.grid(row=3, column=0, sticky='w', pady=6)
        self.value = ttk.Entry(body, width=18)
        self.value.insert(0, '0')
        self.value.grid(row=3, column=1, sticky='w', padx=(12, 0))
        ttk.Label(body, text='Limite superior b:').grid(row=4, column=0, sticky='w', pady=6)
        self.upper = ttk.Entry(body, width=18)
        self.upper.insert(0, '1')
        self.upper.grid(row=4, column=1, sticky='w', padx=(12, 0))
        self.update_inputs()
        ttk.Label(body, text='Use probabilidade entre 0 e 1 nos quantis.\nCauda superior significa P(X > x), inclusive nas distribuições discretas.', wraplength=430).grid(row=5, column=0, columnspan=2, sticky='w', pady=12)
        actions = ttk.Frame(body)
        actions.grid(row=6, column=0, columnspan=2, sticky='e')
        ttk.Button(actions, text='Calcular', command=self.submit).pack(side='left', padx=6)
        ttk.Button(actions, text='Cancelar', command=self.destroy).pack(side='left')
        self.bind('<Escape>', lambda event: self.destroy())
        self.bind('<Return>', lambda event: self.submit())
        parent.center_dialog(self)
        self.grab_set()

    def update_parameters(self, event=None):
        for widget in self.parameter_frame.winfo_children():
            widget.destroy()
        self.parameters = {}
        for row, (key, label, value) in enumerate(DISTRIBUTIONS[self.distribution.get()]):
            ttk.Label(self.parameter_frame, text=label + ':').grid(row=row, column=0, sticky='w', pady=4, padx=(0, 15))
            entry = ttk.Entry(self.parameter_frame, width=18)
            entry.insert(0, str(value))
            entry.grid(row=row, column=1, sticky='w', pady=4)
            self.parameters[key] = entry

    def update_inputs(self, event=None):
        operation = list(OPERATIONS)[self.operation.current()]
        self.input_label.configure(text='Probabilidade p:' if operation in ('quantile', 'isf') else 'Limite inferior a:' if operation == 'interval' else 'Valor x:')
        self.upper.configure(state='normal' if operation == 'interval' else 'disabled')
        if operation in ('quantile', 'isf'):
            self.value.delete(0, 'end')
            self.value.insert(0, '0,95' if operation == 'quantile' else '0,05')

    def submit(self):
        try:
            parameters = {key: float(field.get().strip().replace(',', '.')) for key, field in self.parameters.items()}
            value = float(self.value.get().strip().replace(',', '.'))
            operation = list(OPERATIONS)[self.operation.current()]
            upper = float(self.upper.get().strip().replace(',', '.')) if operation == 'interval' else None
        except ValueError:
            messagebox.showerror('Valores inválidos', 'Confira os parâmetros e os valores informados.', parent=self)
            return
        if self.app.run_distribution(self.distribution.get(), parameters, operation, value, upper):
            self.destroy()
