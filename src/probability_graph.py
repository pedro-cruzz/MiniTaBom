"""Papel de probabilidade normal, com resultado do teste selecionado."""
from copy import deepcopy
import math
import tkinter as tk
from tkinter import ttk
from inference import scientific_stats


class ProbabilityGraph(tk.Toplevel):
    def __init__(self, parent, values, result):
        super().__init__(parent)
        self.transient(parent)
        self.values, self.result = sorted(values), deepcopy(result)
        n=len(self.values)
        self.scores=scientific_stats().norm.ppf([(i-.375)/(n+.25) for i in range(1,n+1)]).tolist()
        self.title('Gráfico de probabilidade normal — ' + result['source'])
        self.geometry('900x600');self.initial_size=(900,600);self.minsize(680,450)
        ttk.Label(self,text='Gráfico de probabilidade normal',style='Title.TLabel').pack(fill='x')
        self.canvas=tk.Canvas(self,background='white',highlightthickness=0)
        self.canvas.pack(fill='both',expand=True)
        ttk.Label(self,text='Posições de Blom · reta normal com média/desvio amostrais · dados do momento da análise',padding=8).pack(fill='x')
        self.canvas.bind('<Configure>',self.draw)

    def draw(self,event=None):
        c=self.canvas;c.delete('all')
        w,h=max(680,c.winfo_width()),max(400,c.winfo_height())
        left,right,top,bottom=70,w-240,55,h-65
        normal=scientific_stats().norm
        n=len(self.values); mean,sd=self.result['mean'],self.result['sd']
        # Trabalha na escala padronizada para preservar coordenadas finitas.
        scale=max(abs(v) for v in self.values)
        xs=[(v-mean)/sd if math.isfinite(v-mean) else (v/scale-mean/scale)/(sd/scale) for v in self.values]
        zs=self.scores
        lo,hi=min(min(xs),zs[0],-2.5759),max(max(xs),zs[-1],2.5759)
        def x(v):return left+(v-lo)/(hi-lo)*(right-left)
        zlo,zhi=min(zs[0],-2.5759),max(zs[-1],2.5759)
        def y(z):return bottom-(z-zlo)/(zhi-zlo)*(bottom-top)
        for probability in [.01,.05,.1,.2,.5,.8,.9,.95,.99]:
            yy=y(float(normal.ppf(probability)))
            c.create_line(left,yy,right,yy,fill='#e3e8ed')
            c.create_text(left-10,yy,text=f'{probability*100:g}',anchor='e')
        for i in range(6):
            xx=lo+(hi-lo)*i/5; raw=mean+sd*xx
            c.create_line(x(xx),top,x(xx),bottom,fill='#edf0f2')
            c.create_text(x(xx),bottom+18,text=f'{raw:.6g}' if math.isfinite(raw) else '')
        c.create_line(left,top,left,bottom,right,bottom,fill='#536477')
        c.create_line(x(zlo),y(zlo),x(zhi),y(zhi),fill='#235e98',width=2)
        step=max(1,math.ceil(n/3000))
        for xx,zz in zip(xs[::step],zs[::step]):
            c.create_oval(x(xx)-3,y(zz)-3,x(xx)+3,y(zz)+3,fill='#bd554e',outline='')
        c.create_text((left+right)/2,h-18,text=self.result['source'])
        c.create_text(20,(top+bottom)/2,text='Percentual',angle=90)
        r=self.result
        p=(f"> {r['p_lower']:g}" if r.get('p_lower') is not None else f"< {r['p_upper']:g}" if r['p'] is None else f"= {r['p']:.6g}")
        text=f"{r.get('method','Anderson–Darling')}\n\nN = {n}\nMédia = {mean:.6g}\nDesvio = {sd:.6g}\n{r.get('stat_label','A²')} = {r['statistic']:.6g}\np {p}"
        if step>1:text+=f'\nExibido 1 a cada {step} pontos;\nteste usa todos os dados.'
        c.create_text(w-220,top,anchor='nw',text=text,width=205,font=('Segoe UI',10))
