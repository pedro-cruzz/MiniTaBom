"""Ícones próprios de 18 px desenhados em pixels, sem recursos externos."""
import tkinter as tk


def create_icons(parent):
    blue, dark, red, light, green = '#2e74a6', '#52616d', '#c6554b', '#c6e0f0', '#488973'
    icons = {}
    for name in ('new', 'open', 'save', 'undo', 'redo', 'table', 'summary', 'histogram',
                 'boxplot', 'groups', 'scatter', 'correlation', 'regression', 'predict',
                 'distribution', 'anova', 'help', 'session', 'options', 'project', 'copy', 'paste', 'clear'):
        image = tk.PhotoImage(master=parent, width=18, height=18)
        def rectangle(x1, y1, x2, y2, color):
            image.put(color, to=(x1, y1, x2 + 1, y2 + 1))
        def line(points, color=blue):
            for (x0, y0), (x1, y1) in zip(points, points[1:]):
                dx, dy = abs(x1 - x0), -abs(y1 - y0)
                sx, sy = 1 if x0 < x1 else -1, 1 if y0 < y1 else -1
                error = dx + dy
                while True:
                    if 0 <= x0 < 18 and 0 <= y0 < 18:
                        image.put(color, to=(x0, y0))
                    if (x0, y0) == (x1, y1):
                        break
                    twice = 2 * error
                    if twice >= dy:
                        error += dy
                        x0 += sx
                    if twice <= dx:
                        error += dx
                        y0 += sy
        if name in ('new', 'session', 'copy', 'paste'):
            if name == 'copy':
                rectangle(2, 1, 12, 13, light)
            rectangle(5, 3, 15, 16, dark)
            rectangle(6, 4, 14, 15, '#ffffff')
            for y in (7, 10, 13):
                line([(8, y), (12, y)], blue)
            if name == 'paste':
                rectangle(7, 1, 12, 4, blue)
        elif name in ('open', 'project'):
            rectangle(2, 4, 8, 6, '#b79235')
            rectangle(2, 6, 15, 15, '#c79d3a')
            rectangle(3, 8, 16, 14, '#f0ce70')
            if name == 'project':
                line([(6, 9), (13, 9)], dark)
                line([(6, 12), (13, 12)], dark)
        elif name == 'save':
            rectangle(2, 2, 15, 15, blue)
            rectangle(5, 2, 12, 7, '#e4eef5')
            rectangle(11, 3, 12, 6, dark)
            rectangle(5, 10, 12, 15, '#ffffff')
        elif name in ('undo', 'redo'):
            points = [(3, 8), (7, 4), (12, 4), (15, 7), (15, 12), (11, 15)]
            arrow = [(3, 3), (3, 8), (8, 8)]
            if name == 'redo':
                points = [(17 - x, y) for x, y in points]
                arrow = [(17 - x, y) for x, y in arrow]
            line(points, blue)
            line(arrow, blue)
        elif name in ('table', 'correlation', 'clear'):
            rectangle(2, 2, 15, 15, dark)
            rectangle(3, 3, 14, 14, '#ffffff')
            rectangle(3, 3, 14, 6, light)
            for x in (7, 11):
                line([(x, 3), (x, 15)], '#8ea8b8')
            for y in (7, 11):
                line([(2, y), (15, y)], '#8ea8b8')
            if name == 'correlation':
                rectangle(3, 7, 6, 10, blue)
                rectangle(8, 11, 10, 14, red)
            if name == 'clear':
                line([(5, 5), (14, 14)], red)
                line([(14, 5), (5, 14)], red)
        elif name == 'summary':
            line([(14, 3), (4, 3), (10, 9), (4, 15), (14, 15)], blue)
            line([(14, 4), (6, 4), (11, 9), (6, 14), (14, 14)], blue)
        elif name in ('histogram', 'anova'):
            line([(2, 2), (2, 15), (16, 15)], dark)
            for x, y in [(4, 9), (8, 4), (12, 7)]:
                rectangle(x, y, x + 2, 14, blue if name == 'histogram' else green)
            if name == 'anova':
                line([(4, 3), (15, 3)], red)
        elif name in ('boxplot', 'groups'):
            for y in ([8] if name == 'boxplot' else [5, 12]):
                line([(2, y), (16, y)], dark)
                line([(2, y - 2), (2, y + 2)], dark)
                line([(16, y - 2), (16, y + 2)], dark)
                rectangle(6, y - 3, 12, y + 3, blue)
                rectangle(7, y - 2, 11, y + 2, light)
                line([(9, y - 3), (9, y + 3)], red)
        elif name in ('scatter', 'regression', 'predict'):
            line([(2, 2), (2, 15), (16, 15)], dark)
            for x, y in [(4, 12), (6, 9), (9, 10), (11, 5), (14, 4)]:
                rectangle(x, y, x + 1, y + 1, blue)
            if name != 'scatter':
                line([(3, 13), (15, 3)], red)
            if name == 'predict':
                rectangle(13, 1, 16, 4, '#d69b36')
        elif name == 'distribution':
            line([(1, 15), (16, 15)], dark)
            line([(1, 14), (3, 13), (5, 10), (7, 4), (9, 2), (11, 5), (13, 11), (16, 14)], blue)
            line([(12, 8), (12, 14)], red)
        elif name == 'options':
            for y, x in [(4, 6), (9, 12), (14, 8)]:
                line([(2, y), (15, y)], dark)
                rectangle(x - 1, y - 2, x + 1, y + 2, blue)
        else:
            rectangle(3, 2, 14, 15, blue)
            line([(6, 5), (7, 4), (11, 4), (12, 6), (9, 9), (9, 11)], '#ffffff')
            rectangle(9, 13, 9, 14, '#ffffff')
        icons[name] = image
    return icons
