from copy import deepcopy
import math
import tkinter as tk
from tkinter import ttk


class FrequencyGraph(tk.Toplevel):
    def __init__(self,parent,result,kind):
        if kind not in ('histogram','bar','pareto','pie'):raise ValueError('Tipo de gráfico inválido.')
        if len(result['table'])>50:raise ValueError('Para o gráfico, use até 50 classes/categorias.')
        super().__init__(parent);self.transient(parent)
        self.result,self.kind=deepcopy(result),kind
        self.title({'histogram':'Histograma','bar':'Gráfico de barras','pareto':'Diagrama de Pareto','pie':'Gráfico de setores'}[kind])
        self.geometry('1000x650');self.initial_size=(1000,650);self.minsize(700,460)
        ttk.Label(self,text=self.title()+' — '+result['source'],style='Title.TLabel').pack(fill='x')
        self.canvas=tk.Canvas(self,background='white',highlightthickness=0)
        scroll=ttk.Scrollbar(self,orient='horizontal',command=self.canvas.xview)
        self.canvas.configure(xscrollcommand=scroll.set);scroll.pack(side='bottom',fill='x');self.canvas.pack(fill='both',expand=True)
        self.canvas.bind('<Configure>',self.draw)

    def draw(self,event=None):
        c=self.canvas;c.delete('all')
        data=self.result['table']
        if self.kind in ('pareto','pie'):data=sorted(data,key=lambda r:-r['count'])
        h=max(540 if self.kind=='pie' else 430,c.winfo_height());w=max(700,c.winfo_width(),len(data)*80+140 if self.kind!='pie' else 500+math.ceil(len(data)/18)*300)
        c.configure(scrollregion=(0,0,w,h))
        palette=['#437eb2','#d68c43','#629b74','#9d75b1','#b75b61','#58a4a8','#b7a448','#73859b']
        if self.kind=='pie':
            angle=0;size=min(h-90,410);box=(40,35,40+size,35+size)
            for i,r in enumerate(data):
                extent=360*r['relative'];color=palette[i%len(palette)]
                c.create_arc(*box,start=angle,extent=extent,fill=color,outline='white',style='pieslice')
                # Tk não desenha arco de extensão exata 360: círculo no caso de uma categoria.
                if len(data)==1:c.create_oval(*box,fill=color,outline='white')
                angle+=extent
                x=500+(i//18)*300;y=45+(i%18)*25
                c.create_rectangle(x,y,x+12,y+12,fill=color,outline='')
                c.create_text(x+22,y+6,anchor='w',text=f"{r['label']}: {r['count']} ({r['percent']:.2f}%)",width=270)
            return
        left,right,top,bottom=75,w-80,45,h-120
        peak=max(r['count'] for r in data) or 1
        for i in range(6):
            y=bottom-(bottom-top)*i/5;c.create_line(left,y,right,y,fill='#e6ebee')
            c.create_text(left-12,y,anchor='e',text=f'{peak*i/5:g}')
            if self.kind=='pareto':c.create_text(right+12,y,anchor='w',text=f'{20*i:g}%')
        c.create_line(left,top,left,bottom,right,bottom,fill='#4e6275')
        step=(right-left)/len(data);points=[];cumulative=0
        for i,r in enumerate(data):
            a,b=left+i*step,left+(i+1)*step;gap=0 if self.kind=='histogram' else step*.15
            y=bottom-r['count']/peak*(bottom-top)
            c.create_rectangle(a+gap,y,b-gap,bottom,fill=palette[0],outline='white')
            c.create_text((a+b)/2,y-10,text=str(r['count']))
            c.create_text((a+b)/2,bottom+12,anchor='n',text=r['label'],width=max(60,step-3),font=('Segoe UI',9))
            cumulative+=r['count'];points += [(a+b)/2,bottom-cumulative/self.result['n']*(bottom-top)]
        if self.kind=='pareto':
            if len(points)>=4:c.create_line(*points,fill='#c24c45',width=2)
            for x,y in zip(points[::2],points[1::2]):c.create_oval(x-3,y-3,x+3,y+3,fill='#c24c45',outline='')
            c.create_text(right,top-18,anchor='e',text='Linha: percentual acumulado')
        c.create_text(22,(top+bottom)/2,text='Frequência',angle=90)
