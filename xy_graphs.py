"""Preparação e cena vetorial para dispersão e séries na ordem da planilha."""
from copy import deepcopy
import math
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import xml.etree.ElementTree as ET

from core import _numeric_value


XY_TITLES = {'scatter': 'Gráfico de dispersão', 'time': 'Gráfico de séries temporais'}
PALETTE = ('#286a9b', '#c04f41', '#318563', '#8b62a2', '#b27c27', '#288b91', '#a45984',
           '#717a31', '#4b74b9', '#ca792c', '#7f599a', '#238c78', '#b85666', '#617ead',
           '#9b7739', '#486f57', '#9a5e4b', '#697b8b', '#a08840', '#59708a')


def prepare_xy(headers, rows, y, x=None, group=None, kind='scatter', connect=False,
               connect_missing=False, x_log=False, y_log=False, title='', x_label='', y_label=''):
    if kind not in XY_TITLES:
        raise ValueError('Tipo de gráfico inválido.')
    selected = [y] + ([x] if kind == 'scatter' else []) + ([group] if group is not None else [])
    if any(type(i) is not int or not 0 <= i < len(headers) for i in selected):
        raise ValueError('Selecione as colunas do gráfico.')
    if group is not None and group in (y, x if kind == 'scatter' else None):
        raise ValueError('Use uma coluna de grupo diferente das variáveis X e Y.')
    groups, omitted = {}, 0
    for line, row in enumerate(rows, 1):
        try:
            xv = _numeric_value(row[x], line) if kind == 'scatter' else float(line)
            yv = _numeric_value(row[y], line)
        except ValueError as error:
            raise ValueError(f'Variáveis do gráfico: {error}') from error
        label = str(row[group]).strip() if group is not None else headers[y]
        if group is not None and label in ('', '*'):
            omitted += 1
            if not connect_missing:
                for series in groups.values():
                    if series['segments'][-1]:
                        series['segments'].append([])
            continue
        series = groups.setdefault(label, dict(label=label, points=[], segments=[[]]))
        if xv is None or yv is None:
            omitted += 1
            if not connect_missing and series['segments'][-1]:
                series['segments'].append([])
            continue
        if (x_log and xv <= 0) or (y_log and yv <= 0):
            raise ValueError(f'Linha {line}: a escala logarítmica requer valores maiores que zero.')
        point = dict(x=xv, y=yv, row=line)
        series['points'].append(point)
        series['segments'][-1].append(point)
    series = [dict(s, segments=[segment for segment in s['segments'] if segment])
              for s in groups.values() if s['points']]
    n = sum(len(s['points']) for s in series)
    if n == 0:
        raise ValueError('Não há observações completas para o gráfico.')
    if n > 20_000 or len(series) > len(PALETTE):
        raise ValueError('Este gráfico aceita até 20.000 pontos e 20 grupos com dados.')
    return dict(kind=kind, title=title.strip() or XY_TITLES[kind] + ' de ' + headers[y],
                x_label=x_label.strip() or (headers[x] if kind == 'scatter' else 'Linha da planilha'),
                y_label=y_label.strip() or headers[y], series=series, n=n, missing=omitted,
                connect=kind == 'time' or bool(connect), connect_missing=bool(connect_missing),
                x_log=bool(x_log), y_log=bool(y_log), group=headers[group] if group is not None else None)


def _axis(values, logarithmic):
    transformed = [math.log10(v) if logarithmic else v for v in values]
    scale = max(abs(v) for v in transformed) or 1.
    low, high = min(transformed) / scale, max(transformed) / scale
    pad = (high - low) * .05 if low != high else .1
    low, high = low - pad, high + pad

    def fraction(v):
        v = math.log10(v) if logarithmic else v
        return (v / scale - low) / (high - low)

    def tick(q):
        value = ((1 - q) * low + q * high) * scale
        try:
            value = 10 ** value if logarithmic else value
        except OverflowError:
            return ''
        return f'{value:.5g}' if math.isfinite(value) and (not logarithmic or value > 0) else ''
    return fraction, tick


def xy_scene(model, width=940, height=540):
    width, height = max(600, width), max(350, height)
    left, right, top, bottom = 92., width - (210 if model['group'] else 40), 65., height - 72.
    points = [p for s in model['series'] for p in s['points']]
    fx, tx = _axis([p['x'] for p in points], model['x_log'])
    fy, ty = _axis([p['y'] for p in points], model['y_log'])
    x = lambda v: left + fx(v) * (right - left)
    y = lambda v: bottom - fy(v) * (bottom - top)
    items = []

    def text(x, y, text, anchor='middle', size=11, color='#41586e', rotation=0):
        items.append(dict(kind='text', x=x, y=y, text=text, anchor=anchor,
                          size=size, fill=color, rotation=rotation))

    def line(coords, stroke='#dfe7ed', width=1, role='axis'):
        items.append(dict(kind='line', coords=coords, stroke=stroke, width=width, role=role))

    text((left + right) / 2, 23, model['title'], size=14, color='#273d56')
    text(right, 44, f"N = {model['n']} · Ausentes = {model['missing']}", anchor='end', size=10)
    if model['kind'] == 'time' and not model['x_log']:
        first, last = min(p['row'] for p in points), max(p['row'] for p in points)
        raw_step = max(1., (last - first) / 5)
        power = 10 ** math.floor(math.log10(raw_step))
        step = int(next(k * power for k in (1, 2, 5, 10) if k * power >= raw_step))
        start = math.ceil(first / step) * step
        x_ticks = [(x(float(v)), str(v)) for v in range(start, last + 1, step)]
    else:
        x_ticks = [(left + i / 5 * (right - left), tx(i / 5)) for i in range(6)]
    for a, label in x_ticks:
        line([a, top, a, bottom])
        text(a, bottom + 18, label, size=10)
    for i in range(6):
        q = i / 5
        b = bottom - q * (bottom - top)
        line([left, b, right, b])
        text(left - 12, b, ty(q), anchor='end', size=10)
    line([left, top, left, bottom, right, bottom], '#7f90a0')
    text((left + right) / 2, height - 24, model['x_label'] + (' (log₁₀)' if model['x_log'] else ''))
    text(23, (top + bottom) / 2, model['y_label'] + (' (log₁₀)' if model['y_log'] else ''), rotation=-90)
    for index, series in enumerate(model['series']):
        color = PALETTE[index]
        if model['connect']:
            for segment in series['segments']:
                if len(segment) > 1:
                    line([v for p in segment for v in (x(p['x']), y(p['y']))], color, 1.5, 'series')
        for point in series['points']:
            items.append(dict(kind='circle', x=x(point['x']), y=y(point['y']), radius=3.5,
                              fill=color, stroke='white',
                              tooltip=f"Linha {point['row']} · {series['label']} · X={point['x']:.9g} · Y={point['y']:.9g}"))
        if model['group']:
            yy = top + index * min(22, (bottom - top) / len(model['series']))
            line([right + 20, yy, right + 40, yy], color, 3)
            label = series['label'] if len(series['label']) <= 22 else series['label'][:19] + '…'
            text(right + 48, yy, label, anchor='start', size=8 if (bottom - top) / len(model['series']) < 16 else 10)
    return dict(width=width, height=height, items=items)


def scene_svg(scene):
    ns = 'http://www.w3.org/2000/svg'
    ET.register_namespace('', ns)
    root = ET.Element(f'{{{ns}}}svg', width=str(scene['width']), height=str(scene['height']),
                      viewBox=f"0 0 {scene['width']} {scene['height']}", role='img')
    ET.SubElement(root, 'rect', width='100%', height='100%', fill='white')
    for item in scene['items']:
        if item['kind'] == 'line':
            coords = item['coords']
            ET.SubElement(root, 'polyline', points=' '.join(f'{a:.5f},{b:.5f}' for a, b in zip(coords[::2], coords[1::2])),
                          fill='none', stroke=item['stroke'], **{'stroke-width': str(item['width'])})
        elif item['kind'] == 'circle':
            element = ET.SubElement(root, 'circle', cx=f"{item['x']:.5f}", cy=f"{item['y']:.5f}",
                                    r=str(item['radius']), fill=item['fill'], stroke=item['stroke'])
            ET.SubElement(element, 'title').text = item['tooltip']
        else:
            attrs = {'x': str(item['x']), 'y': str(item['y']), 'fill': item['fill'],
                     'text-anchor': item['anchor'], 'dominant-baseline': 'central',
                     'font-family': 'Segoe UI, sans-serif', 'font-size': f"{item['size']}pt"}
            if item['rotation']:
                attrs['transform'] = f"rotate({item['rotation']} {item['x']} {item['y']})"
            ET.SubElement(root, 'text', attrs).text = item['text']
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding='unicode') + '\n'


class XYGraphWindow(tk.Toplevel):
    def __init__(self, parent, model):
        super().__init__(parent)
        self.model = deepcopy(model)
        self.transient(parent)
        self.title(model['title'])
        self.initial_size = (980, 640)
        self.geometry('980x640')
        self.minsize(780, 500)
        toolbar = ttk.Frame(self, padding=(8, 6))
        toolbar.pack(fill='x')
        ttk.Label(toolbar, text=XY_TITLES[model['kind']], font=('Segoe UI', 10, 'bold')).pack(side='left')
        ttk.Button(toolbar, text='Exportar SVG…', image=parent.icons['save'], compound='left',
                   command=self.export_svg).pack(side='right')
        self.canvas = tk.Canvas(self, background='white', highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        self.caption = (f"{model['n']} pontos · {model['missing']} linhas omitidas · Dados do momento da criação" +
                        (' · Linhas na ordem da planilha' if model['connect'] else ''))
        self.status = tk.StringVar(self, value=self.caption)
        ttk.Label(self, textvariable=self.status, padding=(8, 6)).pack(fill='x')
        self.canvas.bind('<Configure>', self.draw)
        self.canvas.bind('<Motion>', self.hover)
        self.canvas.bind('<Leave>', lambda e: self.status.set(self.caption))
        self.point_tips = {}

    def draw(self, event=None):
        c = self.canvas
        c.delete('all')
        self.point_tips = {}
        scene = xy_scene(self.model, c.winfo_width(), c.winfo_height())
        for item in scene['items']:
            if item['kind'] == 'line':
                c.create_line(*item['coords'], fill=item['stroke'], width=item['width'], tags=item['role'])
            elif item['kind'] == 'circle':
                x, y, r = item['x'], item['y'], item['radius']
                key = c.create_oval(x - r, y - r, x + r, y + r, fill=item['fill'], outline=item['stroke'], tags='point')
                self.point_tips[key] = item['tooltip']
            else:
                c.create_text(item['x'], item['y'], text=item['text'], fill=item['fill'],
                              anchor={'middle': 'center', 'start': 'w', 'end': 'e'}[item['anchor']],
                              font=('Segoe UI', item['size']), angle=-item['rotation'])

    def hover(self, event=None):
        keys = self.canvas.find_withtag('current')
        self.status.set(self.point_tips.get(keys[-1], self.caption) if keys else self.caption)

    def export_svg(self, path=None):
        if path is None:
            path = filedialog.asksaveasfilename(parent=self, title='Exportar gráfico SVG',
                                               defaultextension='.svg', filetypes=[('SVG', '*.svg')])
        if not path:
            return False
        try:
            scene = xy_scene(self.model, self.canvas.winfo_width(), self.canvas.winfo_height())
            Path(path).write_text(scene_svg(scene), encoding='utf-8')
        except OSError as error:
            messagebox.showerror('Não foi possível exportar', str(error), parent=self)
            return False
        self.status.set('Gráfico exportado em SVG')
        return True
