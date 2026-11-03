import tkinter as tk
from tkinter import ttk, messagebox


class FrequencyDialog(tk.Toplevel):
    def __init__(self,parent,kind='table'):
        super().__init__(parent);self.parent=parent
        self.title('Frequências e gráficos');self.transient(parent);self.resizable(False,False)
        body=ttk.Frame(self,padding=18);body.pack(fill='both',expand=True)
        labels=[f'C{i+1}  {name}' for i,name in enumerate(parent.headers)]
        def label(text,row):ttk.Label(body,text=text).grid(row=row,column=0,sticky='w',padx=(0,14),pady=7)
        label('Variável:',0);self.column=ttk.Combobox(body,values=labels,state='readonly',width=36)
        self.column.current(max(0,parent.column.current()));self.column.grid(row=0,column=1)
        label('Contagens (opcional):',1);self.counts=ttk.Combobox(body,values=['Uma linha por observação']+labels,state='readonly',width=36)
        self.counts.current(0);self.counts.grid(row=1,column=1)
        self.numeric=tk.BooleanVar(self,value=kind=='histogram')
        ttk.Checkbutton(body,text='Agrupar números em classes (regra do material)',variable=self.numeric).grid(row=2,column=0,columnspan=2,sticky='w',pady=8)
        label('Classes desejadas:',3);self.classes=ttk.Entry(body,width=12);self.classes.insert(0,'4');self.classes.grid(row=3,column=1,sticky='w')
        label('Casas decimais (vazio = automático):',4);self.decimals=ttk.Entry(body,width=12);self.decimals.grid(row=4,column=1,sticky='w')
        label('Gráfico:',5);self.graph=ttk.Combobox(body,state='readonly',values=['Somente tabela','Histograma','Barras','Pareto','Setores (pizza)'],width=36)
        self.graph.current(('table','histogram','bar','pareto','pie').index(kind));self.graph.grid(row=5,column=1)
        label('Ordem das categorias:',6);self.order=ttk.Combobox(body,state='readonly',values=['Primeira aparição','Alfabética','Frequência decrescente'],width=36)
        self.order.current(0);self.order.grid(row=6,column=1)
        ttk.Label(body,text='Pareto e setores usam ordem decrescente. Na regra de classes,\n'
                  'passo exato acrescenta uma classe; os demais passos são arredondados\npara cima na precisão escolhida.',wraplength=510).grid(row=7,column=0,columnspan=2,sticky='w',pady=14)
        actions=ttk.Frame(body);actions.grid(row=8,column=0,columnspan=2,sticky='e')
        ttk.Button(actions,text='Cancelar',command=self.destroy).pack(side='right')
        ttk.Button(actions,text='Calcular',command=self.submit).pack(side='right',padx=8)
        self.bind('<Return>',lambda e:self.submit());self.bind('<Escape>',lambda e:self.destroy())
        parent.center_dialog(self);self.grab_set()

    def submit(self):
        try:
            classes=int(self.classes.get()) if self.numeric.get() else 4
            decimals=int(self.decimals.get()) if self.decimals.get().strip() else None
        except ValueError:
            messagebox.showerror('Opções inválidas','Informe classes e casas decimais inteiras.',parent=self);return
        kind=('table','histogram','bar','pareto','pie')[self.graph.current()]
        if kind=='histogram' and not self.numeric.get():
            messagebox.showerror('Opções inválidas','Para histograma, marque o agrupamento numérico em classes.',parent=self);return
        order=('first','sorted','descending')[self.order.current()]
        if kind in ('pareto','pie'):order='descending'
        if self.parent.run_frequency(self.column.current(),numeric=self.numeric.get(),classes=classes,decimals=decimals,
                                     frequency_column=self.counts.current()-1 if self.counts.current()>0 else None,
                                     order=order,kind=kind):self.destroy()
