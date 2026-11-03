"""Gráficos de ajuste e diagnóstico com snapshot dos resultados."""
from copy import deepcopy
import math
import tkinter as tk
from tkinter import ttk
from inference import scientific_stats


class RegressionGraph(tk.Toplevel):
    def __init__(self, parent, result):
        super().__init__(parent)
        self.transient(parent)
        self.result = deepcopy(result)
        n = result['n']
        self.quantiles = scientific_stats().norm.ppf([(i + .625) / (n + .25) for i in range(n)]).tolist()
        ordered = sorted(result['residuals'])
        sd = math.hypot(*ordered) / math.sqrt(max(1, n - 1))
        self.reference = [(self.quantiles[0], self.quantiles[0] * sd), (self.quantiles[-1], self.quantiles[-1] * sd)]
        self.title('Regressão — ajuste e resíduos')
        self.initial_size = (1000, 680)
        self.geometry('1000x680')
        self.minsize(780, 530)
        ttk.Label(self, text='Regressão — ' + result['response'], style='Title.TLabel').pack(fill='x')
        self.canvas = tk.Canvas(self, background='white', highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        ttk.Label(self, text='Diagnóstico visual · dados do momento do ajuste · Q–Q com referência normal', padding=(8, 5)).pack(fill='x')
        self.canvas.bind('<Configure>', self.draw)

    def panel(self, rect, title, x_label, y_label, x_values, y_values, line=None, zero=False):
        c = self.canvas
        left, top, right, bottom = rect
        left, top, right, bottom = left + 68, top + 34, right - 25, bottom - 52
        x_values, y_values = list(x_values), list(y_values)
        xx, yy = x_values[:], y_values[:]
        if line:
            xx += [p[0] for p in line]
            yy += [p[1] for p in line]
        if zero:
            yy.append(0)
        def limits(values):
            scale = max(abs(v) for v in values) or 1
            low, high = min(values) / scale, max(values) / scale
            pad = (high - low) * .08 if high != low else .1
            return scale, low - pad, high + pad
        sx, lo_x, hi_x = limits(xx)
        sy, lo_y, hi_y = limits(yy)
        def x(v):
            return left + (v / sx - lo_x) / (hi_x - lo_x) * (right - left)
        def y(v):
            return bottom - (v / sy - lo_y) / (hi_y - lo_y) * (bottom - top)
        c.create_text((left + right) / 2, top - 18, text=title, font=('Segoe UI', 10, 'bold'), fill='#2f465d')
        for i in range(5):
            q = i / 4
            a, b = left + q * (right - left), bottom - q * (bottom - top)
            c.create_line(left, b, right, b, fill='#e9edf2')
            tx, ty = (lo_x * (1 - q) + hi_x * q) * sx, (lo_y * (1 - q) + hi_y * q) * sy
            c.create_text(a, bottom + 14, text=f'{tx:.4g}' if math.isfinite(tx) else '', font=('Segoe UI', 8), fill='#566371')
            c.create_text(left - 8, b, text=f'{ty:.4g}' if math.isfinite(ty) else '', anchor='e', font=('Segoe UI', 8), fill='#566371')
        c.create_line(left, top, left, bottom, right, bottom, fill='#81909d')
        c.create_text((left + right) / 2, bottom + 36, text=x_label[:55], font=('Segoe UI', 9))
        c.create_text(left - 53, (top + bottom) / 2, text=y_label[:40], angle=90, font=('Segoe UI', 9))
        if zero:
            c.create_line(left, y(0), right, y(0), fill='#bd5b53', dash=(4, 3))
        if line:
            c.create_line(*[coordinate for a, b in line for coordinate in (x(a), y(b))], fill='#b6534c', width=2)
        for a, b in zip(x_values, y_values):
            c.create_oval(x(a) - 3, y(b) - 3, x(a) + 3, y(b) + 3, outline='#245e8c', fill='#9ebed9')

    def draw(self, event=None):
        self.canvas.delete('all')
        width, height = max(740, self.canvas.winfo_width()), max(430, self.canvas.winfo_height())
        r = self.result
        if len(r['predictors']) == 1:
            x = [row[0] for row in r['x']]
            ordered = sorted(zip(x, r['fitted']))
            self.panel((0, 0, width / 2, height / 2), 'Reta ajustada', r['predictors'][0], r['response'],
                       x, r['observed'], line=[ordered[0], ordered[-1]])
        else:
            bounds = [min(r['fitted'] + r['observed']), max(r['fitted'] + r['observed'])]
            self.panel((0, 0, width / 2, height / 2), 'Observados × ajustados', 'Valor ajustado', r['response'],
                       r['fitted'], r['observed'], line=[(v, v) for v in bounds])
        self.panel((width / 2, 0, width, height / 2), 'Resíduos × ajustados', 'Valor ajustado', 'Resíduo',
                   r['fitted'], r['residuals'], zero=True)
        ordered = sorted(r['residuals'])
        self.panel((0, height / 2, width / 2, height), 'Q–Q dos resíduos', 'Quantil normal teórico', 'Resíduo', self.quantiles, ordered, line=self.reference)
        self.panel((width / 2, height / 2, width, height), 'Resíduos na ordem dos dados', 'Linha da planilha', 'Resíduo',
                   r['row_numbers'], r['residuals'], zero=True)
