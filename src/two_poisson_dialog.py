import math
import tkinter as tk
from tkinter import ttk,messagebox
from basic_inference import parse_count
from two_poisson import TITLE


class TwoPoissonDialog(tk.Toplevel):
    def __init__(self,parent):
        super().__init__(parent);self.parent=parent
        self.title(TITLE);self.transient(parent);self.resizable(False,False)
        body=ttk.Frame(self,padding=16);body.pack(fill='both',expand=True)
        ttk.Label(body,text=TITLE,style='Title.TLabel').pack(fill='x')
        tabs=ttk.Notebook(body);tabs.pack(fill='both',expand=True,pady=12)
        data,options=ttk.Frame(tabs,padding=12),ttk.Frame(tabs,padding=12)
        tabs.add(data,text='Dados',image=parent.icons['table'],compound='left')
        tabs.add(options,text='Opções',image=parent.icons['options'],compound='left')
        self.source=ttk.Combobox(data,state='readonly',width=38,values=['Contagens em duas colunas','Contagens e coluna de grupo','Dados resumidos'])
        self.source.current(0);self.source.pack(anchor='w',pady=(0,12));self.source.bind('<<ComboboxSelected>>',lambda e:self.toggle_source())
        self.frames=[ttk.Frame(data) for _ in range(3)]
        labels=[f'C{i+1}  {name}' for i,name in enumerate(parent.headers)]
        def picker(frame,row,label,index):
            ttk.Label(frame,text=label).grid(row=row,column=0,sticky='w',padx=(0,12),pady=7)
            control=ttk.Combobox(frame,state='readonly',values=labels,width=38);control.current(min(index,len(labels)-1))
            control.grid(row=row,column=1,sticky='w');return control
        self.first=picker(self.frames[0],0,'Primeira amostra:',0);self.second=picker(self.frames[0],1,'Segunda amostra:',1)
        self.response=picker(self.frames[1],0,'Contagens:',0);self.group=picker(self.frames[1],1,'Grupo:',1)
        self.events=[];self.ns=[]
        for i in range(2):
            self.events.append(self.entry(self.frames[2],i*2,f'Ocorrências da amostra {i+1}:','0'))
            self.ns.append(self.entry(self.frames[2],i*2+1,f'Número de observações {i+1}:','10'))
        lengths=ttk.Frame(data);lengths.pack(fill='x',side='bottom',pady=(12,0))
        self.length1=self.entry(lengths,0,'Exposição por observação — amostra 1:','1')
        self.length2=self.entry(lengths,1,'Exposição por observação — amostra 2:','1')
        ttk.Label(options,text='Comparar:').grid(row=0,column=0,sticky='w')
        self.measure=ttk.Combobox(options,state='readonly',width=38,values=['Taxas por unidade de exposição','Médias de contagens por observação'])
        self.measure.current(0);self.measure.grid(row=0,column=1,sticky='w',pady=7)
        self.confidence=self.entry(options,1,'Confiança (95 ou 0,95):','95')
        self.perform_test=tk.BooleanVar(self,value=True)
        ttk.Checkbutton(options,text='Realizar teste de hipótese',variable=self.perform_test,command=self.toggle_test).grid(row=2,column=0,columnspan=2,sticky='w',pady=9)
        self.null=self.entry(options,3,'Diferença hipotética (primeira − segunda):','0')
        ttk.Label(options,text='Alternativa / direção do IC:').grid(row=4,column=0,sticky='w')
        self.alternative=ttk.Combobox(options,state='readonly',values=['Diferente de (≠)','Menor que (<)','Maior que (>)'],width=24)
        self.alternative.current(0);self.alternative.grid(row=4,column=1,sticky='w',pady=8)
        self.pooled=tk.BooleanVar(self,value=False)
        self.pooled_control=ttk.Checkbutton(options,text='Usar taxa combinada no teste normal (exige diferença zero)',variable=self.pooled)
        self.pooled_control.grid(row=5,column=0,columnspan=2,sticky='w',pady=10)
        ttk.Label(body,text='Contagens inteiras não negativas; exposição igual dentro de cada amostra.\n'
                  'O teste exato é calculado para diferença zero. O intervalo usa aproximação normal.\n'
                  'Taxas usam a exposição; médias comparam contagens por observação.',wraplength=680,foreground='#536477').pack(fill='x')
        actions=ttk.Frame(body);actions.pack(fill='x',pady=(12,0))
        ttk.Button(actions,text='Cancelar',command=self.destroy).pack(side='right')
        ttk.Button(actions,text='Calcular',command=self.submit,style='Accent.TButton').pack(side='right',padx=8)
        self.toggle_source();self.bind('<Escape>',lambda e:self.destroy());self.bind('<Return>',lambda e:self.submit())
        parent.center_dialog(self);self.grab_set()

    @staticmethod
    def entry(frame,row,label,value):
        ttk.Label(frame,text=label).grid(row=row,column=0,sticky='w',padx=(0,12),pady=7)
        entry=ttk.Entry(frame,width=24);entry.insert(0,value);entry.grid(row=row,column=1,sticky='w');return entry

    def toggle_source(self):
        for i,frame in enumerate(self.frames):frame.pack(fill='x') if i==self.source.current() else frame.pack_forget()

    def toggle_test(self):
        self.null.configure(state='normal' if self.perform_test.get() else 'disabled')
        self.pooled_control.configure(state='normal' if self.perform_test.get() else 'disabled')

    def submit(self):
        try:
            number=lambda e:float(e.get().strip().replace(',','.'))
            confidence=number(self.confidence)
            if 0<confidence<1:confidence*=100
            if not math.isfinite(confidence):raise ValueError('Use confiança finita.')
            options=dict(lengths=[number(self.length1),number(self.length2)],null=number(self.null) if self.perform_test.get() else 0.,
                         confidence=confidence,alternative=('two-sided','less','greater')[self.alternative.current()],
                         pooled=self.pooled.get() if self.perform_test.get() else False,measure=('rate','mean')[self.measure.current()],
                         perform_test=self.perform_test.get())
            kind=('columns','stacked','summary')[self.source.current()]
            if kind=='summary':options['summaries']=[dict(events=parse_count(e.get(),'Ocorrências'),n=parse_count(n.get(),'Número de observações',1)) for e,n in zip(self.events,self.ns)]
            else:options['columns']=[self.first.current(),self.second.current()] if kind=='columns' else [self.response.current(),self.group.current()]
            if self.parent.run_two_poisson(input_kind=kind,**options):self.destroy()
        except (ValueError,ArithmeticError) as error:messagebox.showerror('Dados inválidos',str(error),parent=self)
