"""Gráficos independentes, desenhados a partir de uma cópia dos dados."""
import math
import tkinter as tk
from tkinter import ttk
from core import histogram, boxplot


class GroupGraphWindow(tk.Toplevel):
    def __init__(self, parent, groups, response='Valores'):
        prepared = [dict(label=g['label'], values=list(g['values']), box=boxplot(g['values'])) for g in groups]
        if len(prepared) < 2:
            raise ValueError('Selecione pelo menos dois grupos para comparar.')
        super().__init__(parent)
        self.transient(parent)
        self.groups, self.response = prepared, response
        self.title('Boxplots comparativos')
        self.initial_size = (900, 580)
        self.geometry('900x580')
        self.minsize(650, 440)
        ttk.Label(self, text='Boxplots comparativos · escala comum', style='Title.TLabel').pack(fill='x')
        frame = ttk.Frame(self)
        frame.pack(fill='both', expand=True)
        self.canvas = tk.Canvas(frame, background='white', highlightthickness=0)
        sy = ttk.Scrollbar(frame, orient='vertical', command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=sy.set)
        sy.pack(side='right', fill='y')
        self.canvas.pack(fill='both', expand=True)
        ttk.Label(self, text='Caixa: Q1–Q3 · linha: mediana · pontos vermelhos: observações além de 1,5 IQR', padding=(10, 8)).pack(fill='x')
        self.canvas.bind('<Configure>', self.draw)
        self.canvas.bind('<MouseWheel>', lambda event: self.canvas.yview_scroll(-int(event.delta / 120), 'units'))

    def draw(self, event=None):
        c = self.canvas
        c.delete('all')
        width = max(500, c.winfo_width())
        height = max(c.winfo_height(), 130 + 74 * len(self.groups))
        c.configure(scrollregion=(0, 0, width, height))
        left, right, top, bottom = 205, width - 40, 45, height - 65
        values = [value for g in self.groups for value in g['values']]
        scale = max(1, max(abs(v) for v in values))
        low, high = min(values) / scale, max(values) / scale
        padding = (high - low) * .08 if high != low else max(.1, abs(low) * .1)
        low, high = low - padding, high + padding
        def x(value):
            return left + (value / scale - low) / (high - low) * (right - left)
        for i in range(6):
            ratio = i / 5
            tick = left + ratio * (right - left)
            value = ((1 - ratio) * low + ratio * high) * scale
            c.create_line(tick, top, tick, bottom, fill='#e7edf3')
            c.create_text(tick, bottom + 18, text=f'{value:.5g}' if math.isfinite(value) else '', fill='#536477')
        c.create_line(left, bottom, right, bottom, fill='#718296')
        c.create_text((left + right) / 2, height - 18, text=self.response, fill='#365777', font=('Segoe UI', 10))
        palette = ('#d8e9f7', '#dcece6', '#f4e6d3', '#e7e0f1')
        step = (bottom - top) / len(self.groups)
        for index, group in enumerate(self.groups):
            data, y = group['box'], top + step * (index + .5)
            label = group['label'] if len(group['label']) <= 25 else group['label'][:22] + '…'
            c.create_text(left - 18, y - 9, text=label, anchor='e', fill='#365777', font=('Segoe UI', 10, 'bold'))
            c.create_text(left - 18, y + 10, text=f"N = {len(group['values'])}", anchor='e', fill='#62758a', font=('Segoe UI', 9))
            c.create_line(x(data['low']), y, x(data['high']), y, fill='#365777', width=2)
            for value in (data['low'], data['high']):
                c.create_line(x(value), y - 12, x(value), y + 12, fill='#365777', width=2)
            c.create_rectangle(x(data['q1']), y - 20, x(data['q3']), y + 20,
                               fill=palette[index % len(palette)], outline='#365777', width=2)
            c.create_line(x(data['median']), y - 20, x(data['median']), y + 20, fill='#254463', width=3)
            for value in data['outliers']:
                c.create_oval(x(value) - 4, y - 4, x(value) + 4, y + 4, fill='#b54b45', outline='')


class GraphWindow(tk.Toplevel):
    def __init__(self, parent, kind, column, values):
        if kind not in ('Histograma', 'Boxplot'):
            raise ValueError('Tipo de gráfico não suportado.')
        model = histogram(values) if kind == 'Histograma' else boxplot(values)
        super().__init__(parent)
        self.transient(parent)
        self.kind, self.column, self.values = kind, column, list(values)
        self.title(f'{kind} — {column}')
        self.initial_size = (840, 560)
        self.geometry('840x560')
        self.minsize(600, 420)
        self.model = model
        ttk.Label(self, text=f'{kind} de {column}', style='Title.TLabel').pack(fill='x')
        self.canvas = tk.Canvas(self, background='white', highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        caption = ('Sturges · máximo de 30 classes' if kind == 'Histograma'
                   else 'Caixa: Q1–Q3 · linha: mediana · pontos vermelhos: valores além de 1,5 IQR')
        ttk.Label(self, text=caption, padding=(10, 8)).pack(fill='x')
        self.canvas.bind('<Configure>', self.draw)

    def draw(self, event=None):
        c = self.canvas
        c.delete('all')
        width, height = max(400, c.winfo_width()), max(250, c.winfo_height())
        left, right, top, bottom = 90, width - 40, 50, height - 65
        c.create_text(right, 22, text=f'N = {len(self.values)}', anchor='e', fill='#536477', font=('Segoe UI', 10))
        # Normalizar antes da subtração evita overflow na escala visual.
        scale = max(1, max(abs(v) for v in self.values))
        lo, hi = min(self.values) / scale, max(self.values) / scale
        if lo == hi:
            pad = max(abs(lo) * .1, .1)
        else:
            pad = (hi - lo) * .08
        lo, hi = lo - pad, hi + pad
        def x(value):
            return left + (value / scale - lo) / (hi - lo) * (right - left)
        for i in range(6):
            ratio = i / 5
            value = lo * (1 - ratio) + hi * ratio
            # Escalas extremas podem estender o eixo além dos floats finitos.
            label = value * scale
            tick = left + ratio * (right - left)
            c.create_line(tick, top, tick, bottom, fill='#e7edf3')
            c.create_text(tick, bottom + 18, text=f'{label:.5g}' if math.isfinite(label) else '', fill='#536477', font=('Segoe UI', 9))
        c.create_line(left, bottom, right, bottom, fill='#718296')
        c.create_text((left + right) / 2, height - 20, text=self.column, font=('Segoe UI', 10))
        if self.kind == 'Histograma':
            edges, counts = self.model
            ceiling = max(counts)
            for i in range(6):
                count = ceiling * i / 5
                y = bottom - (bottom - top) * i / 5
                c.create_line(left, y, right, y, fill='#edf1f5')
                c.create_text(left - 12, y, text=f'{count:g}', anchor='e', fill='#536477')
            c.create_text(25, (top + bottom) / 2, text='Frequência', angle=90, fill='#536477')
            c.create_line(left, top, left, bottom, fill='#718296')
            for i, count in enumerate(counts):
                a, b = x(edges[i]), x(edges[i + 1])
                if a == b:
                    a, b = x(edges[i]) - 24, x(edges[i]) + 24
                y = bottom - count / ceiling * (bottom - top)
                c.create_rectangle(a, y, b, bottom, fill='#6596bd', outline='white')
                c.create_text((a + b) / 2, y - 12, text=str(count), fill='#365777')
        else:
            data = self.model
            y = (top + bottom) / 2
            c.create_line(x(data['low']), y, x(data['high']), y, fill='#365777', width=2)
            for value in (data['low'], data['high']):
                c.create_line(x(value), y - 16, x(value), y + 16, fill='#365777', width=2)
            c.create_rectangle(x(data['q1']), y - 38, x(data['q3']), y + 38,
                               fill='#d8e9f7', outline='#365777', width=2)
            c.create_line(x(data['median']), y - 38, x(data['median']), y + 38, fill='#254463', width=3)
            for value in data['outliers']:
                c.create_oval(x(value) - 4, y - 4, x(value) + 4, y + 4, fill='#b54b45', outline='')
            c.create_text((left + right) / 2, top + 5,
                text=f"Q1 = {data['q1']:.6g}    Mediana = {data['median']:.6g}    Q3 = {data['q3']:.6g}",
                fill='#536477', font=('Segoe UI', 10))
