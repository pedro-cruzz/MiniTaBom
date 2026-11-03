import re
import tkinter as tk
from tkinter import ttk,messagebox


class PercentileDialog(tk.Toplevel):
    def __init__(self,parent):
        super().__init__(parent);self.parent=parent
        self.title('Percentis e decis da amostra');self.transient(parent);self.resizable(False,False)
        body=ttk.Frame(self,padding=18);body.pack(fill='both',expand=True)
        ttk.Label(body,text='Variável numérica:').pack(anchor='w')
        self.column=ttk.Combobox(body,state='readonly',width=46,values=[f'C{i+1}  {h}' for i,h in enumerate(parent.headers)])
        self.column.current(max(0,parent.column.current()));self.column.pack(fill='x',pady=7)
        ttk.Label(body,text='Percentuais separados por ponto e vírgula:').pack(anchor='w')
        self.percentages=ttk.Entry(body,width=46);self.percentages.insert(0,'10; 25; 50; 75; 90');self.percentages.pack(fill='x',pady=7)
        ttk.Button(body,text='Todos os decis (10% a 90%)',command=self.deciles).pack(anchor='w',pady=6)
        self.method=ttk.Combobox(body,state='readonly',width=54,
            values=['Exclusivo: (N+1)p; posição fora da amostra indefinida','Inclusivo: 1+(N−1)p','(N+1)p com extremos limitados ao mínimo/máximo'])
        self.method.current(0);self.method.pack(fill='x',pady=10)
        actions=ttk.Frame(body);actions.pack(fill='x',pady=10)
        ttk.Button(actions,text='Cancelar',command=self.destroy).pack(side='right')
        ttk.Button(actions,text='Calcular',command=self.submit).pack(side='right',padx=8)
        self.bind('<Return>',lambda e:self.submit());self.bind('<Escape>',lambda e:self.destroy())
        parent.center_dialog(self);self.grab_set()

    def deciles(self):
        self.percentages.delete(0,'end');self.percentages.insert(0,'; '.join(str(p) for p in range(10,100,10)))

    def submit(self):
        try:values=[float(s.replace(',','.')) for s in re.split(r'[;\s]+',self.percentages.get().strip()) if s]
        except ValueError:
            messagebox.showerror('Percentis inválidos','Use percentuais numéricos separados por ponto e vírgula.',parent=self);return
        if self.parent.run_percentiles(self.column.current(),values,('exclusive','inclusive','clamped')[self.method.current()]):self.destroy()
