import math
import tkinter as tk
from tkinter import ttk, messagebox
from descriptive_dialog import DescriptiveDialog


class LinearDialog(tk.Toplevel):
    def __init__(self, parent, mode):
        super().__init__(parent)
        self.app, self.mode = parent, mode
        self.title('Correlação' if mode == 'correlation' else 'Regressão linear')
        self.transient(parent)
        self.resizable(False, False)
        body = ttk.Frame(self, padding=12)
        body.pack(fill='both', expand=True)
        tabs = ttk.Notebook(body)
        tabs.pack(fill='both', expand=True)
        data, options = ttk.Frame(tabs, padding=12), ttk.Frame(tabs, padding=12)
        tabs.add(data, text='Dados', image=parent.icons['table'], compound='left')
        tabs.add(options, text='Opções e resultados', image=parent.icons['options'], compound='left')
        self.variables = DescriptiveDialog.column_list(data, parent.headers,
            'Variáveis numéricas:' if mode == 'correlation' else 'Preditores numéricos:', 0)
        self.variables.selection_set(0, min(1, len(parent.headers) - 1))
        self.response = None
        self.method, self.missing = tk.StringVar(value='pearson'), tk.StringVar(value='pairwise')
        self.show_graph = tk.BooleanVar(value=mode == 'regression')
        self.observations = tk.BooleanVar(value=False)
        self.store = tk.BooleanVar(value=False)
        self.check_bivariate = tk.BooleanVar(value=False)
        if mode == 'regression':
            self.variables.selection_clear(0, 'end')
            self.variables.selection_set(1 if len(parent.headers) > 1 else 0)
            side = ttk.Frame(data, padding=(12, 0))
            side.grid(row=0, column=1, sticky='nsew')
            ttk.Label(side, text='Resposta:').pack(anchor='w', pady=(0, 6))
            self.response = ttk.Combobox(side, state='readonly', width=28,
                values=[f'C{i + 1}  {h}' for i, h in enumerate(parent.headers)])
            self.response.pack(fill='x')
            self.response.current(0)
            ttk.Label(side, text='Modelo com constante e efeitos lineares.\nSelecione um ou mais preditores.\nAs linhas com qualquer ausente são omitidas.',
                      wraplength=245, justify='left').pack(anchor='w', pady=18)
            ttk.Checkbutton(options, text='Mostrar gráficos de ajuste e resíduos', variable=self.show_graph).grid(row=1, column=0, columnspan=2, sticky='w', pady=8)
            ttk.Checkbutton(options, text='Mostrar tabela de observações e diagnósticos', variable=self.observations).grid(row=2, column=0, columnspan=2, sticky='w', pady=8)
            ttk.Checkbutton(options, text='Armazenar ajustados, resíduos e diagnósticos na planilha', variable=self.store).grid(row=3,column=0,columnspan=2,sticky='w',pady=8)
        else:
            ttk.Label(data, text='Use Ctrl ou Shift para selecionar duas ou mais colunas.').grid(row=1, column=0, sticky='w', pady=(10, 0))
            for row, (label, value) in enumerate([('Pearson — relação linear', 'pearson'), ('Spearman — postos médios nos empates', 'spearman')], 1):
                ttk.Radiobutton(options, text=label, variable=self.method, value=value,
                                command=self.update_confidence).grid(row=row, column=0, columnspan=2, sticky='w', pady=5)
            ttk.Separator(options).grid(row=3, column=0, columnspan=2, sticky='ew', pady=12)
            ttk.Radiobutton(options, text='Excluir ausentes por par de variáveis', variable=self.missing, value='pairwise').grid(row=4, column=0, columnspan=2, sticky='w', pady=5)
            ttk.Radiobutton(options, text='Usar somente linhas completas nas variáveis selecionadas', variable=self.missing, value='listwise').grid(row=5, column=0, columnspan=2, sticky='w', pady=5)
            ttk.Label(options, text='IC de Fisher para Pearson com N > 3. IC de Spearman ainda indisponível.', wraplength=480).grid(row=6, column=0, columnspan=2, sticky='w', pady=12)
            ttk.Checkbutton(options,text='Diagnóstico bivariado de Mardia (selecionar duas variáveis)',variable=self.check_bivariate).grid(row=7,column=0,columnspan=2,sticky='w',pady=8)
        ttk.Label(options, text='Nível de confiança (%):').grid(row=0, column=0, sticky='w', pady=(0, 12), padx=(0, 12))
        self.confidence = ttk.Entry(options, width=10)
        self.confidence.insert(0, '95')
        self.confidence.grid(row=0, column=1, sticky='w', pady=(0, 12))
        actions = ttk.Frame(body)
        actions.pack(fill='x', pady=(12, 0))
        ttk.Button(actions, text='Cancelar', command=self.destroy).pack(side='right')
        ttk.Button(actions, text='Calcular', command=self.submit).pack(side='right', padx=6)
        self.bind('<Escape>', lambda event: self.destroy())
        self.bind('<Return>', lambda event: self.submit())
        parent.center_dialog(self)
        self.grab_set()
        self.variables.focus_set()

    def update_confidence(self):
        self.confidence.configure(state='disabled' if self.method.get() == 'spearman' else 'normal')

    def submit(self):
        try:
            confidence = float(self.confidence.get().strip().replace(',', '.'))
            if not math.isfinite(confidence) or not 0 < confidence < 100:
                raise ValueError
        except ValueError:
            messagebox.showerror('Opção inválida', 'Informe confiança entre 0 e 100, sem os extremos.', parent=self)
            return
        columns = list(self.variables.curselection())
        if self.mode == 'correlation':
            done = self.app.run_correlation(columns, method=self.method.get(), missing=self.missing.get(), confidence=confidence,check_bivariate=self.check_bivariate.get())
        else:
            done = self.app.run_regression(self.response.current(), columns, confidence=confidence,
                                          show_graph=self.show_graph.get(), observations=self.observations.get(),store=self.store.get())
        if done:
            self.destroy()
