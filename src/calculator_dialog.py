import tkinter as tk
from tkinter import ttk


class CalculatorDialog(tk.Toplevel):
    def __init__(self,parent):
        super().__init__(parent);self.parent=parent
        self.title('Calculadora de colunas');self.transient(parent);self.resizable(False,False)
        body=ttk.Frame(self,padding=18);body.pack(fill='both',expand=True)
        ttk.Label(body,text='Armazenar resultado em nova coluna:').pack(anchor='w')
        self.name=ttk.Entry(body,width=45);self.name.insert(0,'Calculado');self.name.pack(fill='x',pady=6)
        ttk.Label(body,text='Expressão:').pack(anchor='w')
        self.expression=ttk.Entry(body,width=45);self.expression.insert(0,'C1 - C2' if len(parent.headers)>1 else 'C1')
        self.expression.pack(fill='x',pady=6)
        ttk.Label(body,text='Exemplos: C1 - C2; (C1 + C2) / 2; sqrt(C1); round(C1, 2).\n'
                  'Constantes usam ponto decimal. Ausente em uma entrada gera ausente.\n'
                  'Funções: abs, sqrt, log, log10, exp, round.',wraplength=480).pack(anchor='w',pady=10)
        ttk.Label(body,text='\n'.join(f'C{i+1}: {h}' for i,h in enumerate(parent.headers[:15])),wraplength=480).pack(anchor='w')
        actions=ttk.Frame(body);actions.pack(fill='x',pady=12)
        ttk.Button(actions,text='Cancelar',command=self.destroy).pack(side='right')
        ttk.Button(actions,text='Calcular',command=self.submit).pack(side='right',padx=8)
        self.bind('<Return>',lambda e:self.submit());self.bind('<Escape>',lambda e:self.destroy())
        parent.center_dialog(self);self.grab_set();self.expression.focus_set()

    def submit(self):
        if self.parent.run_calculator(self.expression.get(),self.name.get()):self.destroy()
