import tkinter as tk
from tkinter import ttk
from group_dialog import GroupSelector
from study_tests import TITLES


class StudyTestDialog(tk.Toplevel):
    def __init__(self, parent, mode):
        super().__init__(parent)
        self.parent, self.mode = parent, mode
        self.title(TITLES[mode])
        self.transient(parent)
        self.resizable(False, False)
        body = ttk.Frame(self, padding=16)
        body.pack(fill='both', expand=True)
        tabs = ttk.Notebook(body)
        tabs.pack(fill='both', expand=True)
        data, options = ttk.Frame(tabs, padding=14), ttk.Frame(tabs, padding=14)
        tabs.add(data, text='Dados', image=parent.icons['table'], compound='left')
        tabs.add(options, text='Opções', image=parent.icons['options'], compound='left')
        self.selector = None
        if mode == 'wilcoxon':
            labels = [f'C{i+1}  {name}' for i,name in enumerate(parent.headers)]
            ttk.Label(data, text='Primeira amostra:').grid(row=0,column=0,pady=8,padx=8)
            ttk.Label(data, text='Segunda amostra:').grid(row=1,column=0,pady=8,padx=8)
            self.first, self.second = [ttk.Combobox(data,values=labels,state='readonly',width=32) for _ in range(2)]
            self.first.grid(row=0,column=1); self.second.grid(row=1,column=1)
            self.first.current(0)
            if len(labels)>1: self.second.current(1)
            ttk.Label(data,text='Diferença = primeira − segunda. Ausentes excluem o par inteiro.').grid(row=2,column=0,columnspan=2,pady=16)
        else:
            self.selector = GroupSelector(data, parent.headers)
            self.selector.pack(fill='both', expand=True)
        self.alternative = ttk.Combobox(options, state='readonly', values=['Bilateral','Primeira menor que segunda','Primeira maior que segunda'],width=34)
        self.alternative.current(0)
        self.method = ttk.Combobox(options, state='readonly', values=['Automático','Exato (sem empates/zeros)','Aproximação normal'],width=34)
        self.method.current(0)
        self.correction = tk.BooleanVar(self,value=True)
        self.zero = ttk.Combobox(options,state='readonly',values=['Excluir zeros (Wilcox)','Pratt','Dividir postos zero (zsplit)'],width=34)
        self.zero.current(0)
        self.center = ttk.Combobox(options,state='readonly',values=['Levene — mediana (Brown–Forsythe)','Levene — média','Bartlett — pressupõe normalidade'],width=43)
        self.center.current(0)
        if mode in ('mannwhitney','wilcoxon'):
            ttk.Label(options,text='Hipótese alternativa:').pack(anchor='w',pady=6);self.alternative.pack(anchor='w')
            ttk.Label(options,text='Cálculo de probabilidade:').pack(anchor='w',pady=6);self.method.pack(anchor='w')
            ttk.Checkbutton(options,text='Correção de continuidade na aproximação',variable=self.correction).pack(anchor='w',pady=12)
            if mode=='wilcoxon':
                ttk.Label(options,text='Diferenças iguais a zero:').pack(anchor='w');self.zero.pack(anchor='w',pady=8)
        elif mode=='variances':
            ttk.Label(options,text='Método para todos os grupos simultaneamente:').pack(anchor='w',pady=8)
            self.center.pack(anchor='w')
        else:
            ttk.Label(options,text='Kruskal–Wallis: teste global com correção de empates.\n'
                      'A probabilidade usa aproximação qui-quadrado.\nO teste global não identifica os pares diferentes.',wraplength=450).pack(anchor='w')
        actions=ttk.Frame(body);actions.pack(fill='x',pady=(14,0))
        ttk.Button(actions,text='Cancelar',command=self.destroy).pack(side='right')
        ttk.Button(actions,text='Calcular',style='Accent.TButton',command=self.submit).pack(side='right',padx=8)
        self.bind('<Return>',lambda e:self.submit());self.bind('<Escape>',lambda e:self.destroy())
        parent.center_dialog(self);self.grab_set()

    def submit(self):
        selection = self.selector.selection() if self.selector else dict(columns=[self.first.current(),self.second.current()])
        if self.parent.run_study(self.mode,**selection, alternative=('two-sided','less','greater')[self.alternative.current()],
                                 method=('auto','exact','asymptotic')[self.method.current()],correction=self.correction.get(),
                                 zero_method=('wilcox','pratt','zsplit')[self.zero.current()],
                                 center=('median','mean','bartlett')[self.center.current()]):
            self.destroy()
