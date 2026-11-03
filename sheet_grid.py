"""Grade de células com cabeçalhos fixos e desenho limitado à área visível."""
import math
from bisect import bisect_right
import tkinter as tk
from tkinter import font


class SheetGrid(tk.Canvas):
    gutter = 44
    header_height = 48
    row_height = 23
    column_width = 116

    def __init__(self, parent):
        super().__init__(parent, background='white', highlightthickness=0,
                         borderwidth=0, takefocus=True)
        self.headers, self.rows = [], []
        self.active = (0, 0)
        self.selection = (0, 0, 0, 0)
        self.column_widths = []
        self.edges = [0]
        self.top_row, self.left_pixel = 0, 0
        self.yset = self.xset = lambda *args: None
        self.text_font = font.Font(self, family='Segoe UI', size=9)
        self.header_font = font.Font(self, family='Segoe UI', size=9, weight='bold')

    def sync_columns(self):
        self.column_widths = (self.column_widths + [self.column_width] * len(self.headers))[:len(self.headers)]
        self.edges = [0]
        for width in self.column_widths:
            self.edges.append(self.edges[-1] + width)

    def resize_column(self, column, width):
        self.column_widths[column] = max(60, min(600, int(width)))
        self.sync_columns()
        self.redraw()

    def fit_column(self, column):
        widths = [self.header_font.measure(f'C{column + 1}'), self.text_font.measure(self.headers[column])]
        widths.extend(self.text_font.measure(str(row[column]).replace('\n', ' ').replace('\r', ' ')) for row in self.rows)
        self.resize_column(column, max(widths) + 18)

    def column_boundary(self, x):
        if x <= self.gutter:
            return None
        point = x - self.gutter + self.left_pixel
        at = bisect_right(self.edges, point)
        for boundary in (at - 1, at):
            if 0 < boundary < len(self.edges) and abs(self.edges[boundary] - point) <= 4:
                return boundary - 1
        return None

    def column_at(self, x):
        column = bisect_right(self.edges, x - self.gutter + self.left_pixel) - 1
        return column if 0 <= column < len(self.headers) else None

    @property
    def row_count(self):
        return max(40, len(self.rows) + 1, self.active[0] + 1)

    def visible_rows(self):
        return max(1, (self.winfo_height() - self.header_height) // self.row_height)

    def viewport_width(self):
        return max(1, self.winfo_width() - self.gutter)

    def clamp_offsets(self):
        self.top_row = min(max(0, self.top_row), max(0, self.row_count - self.visible_rows()))
        self.left_pixel = min(max(0, self.left_pixel),
                              max(0, self.edges[-1] - self.viewport_width()))

    def reveal(self, row, column):
        if row < self.top_row:
            self.top_row = row
        elif row >= self.top_row + self.visible_rows():
            self.top_row = row - self.visible_rows() + 1
        left, right = self.edges[column], self.edges[column + 1]
        if left < self.left_pixel:
            self.left_pixel = left
        elif right > self.left_pixel + self.viewport_width():
            self.left_pixel = min(left, right - self.viewport_width())
        self.clamp_offsets()

    def bbox(self, item, column=None):
        if column is None:
            return super().bbox(item)
        row, col = int(item), int(column)
        x = self.gutter + self.edges[col] - self.left_pixel
        y = self.header_height + (row - self.top_row) * self.row_height
        right = min(self.winfo_width(), x + self.column_widths[col])
        bottom = min(self.winfo_height(), y + self.row_height)
        x, y = max(self.gutter, x), max(self.header_height, y)
        if right <= x or bottom <= y:
            return ()
        return x, y, right - x, bottom - y

    def identify_row(self, y):
        if y < self.header_height or y >= self.winfo_height():
            return ''
        return str(self.top_row + (y - self.header_height) // self.row_height)

    def identify_column(self, x):
        if x < self.gutter:
            return '#0'
        col = self.column_at(x)
        return f'#{col + 1}' if col is not None else ''

    def identify_region(self, x, y):
        return 'heading' if 0 <= y < self.header_height else 'cell'

    def yview(self, *args):
        if not args:
            return self.top_row / self.row_count, min(1, (self.top_row + self.visible_rows()) / self.row_count)
        if args[0] == 'moveto':
            self.top_row = round(float(args[1]) * self.row_count)
        else:
            self.top_row += int(args[1]) * (max(1, self.visible_rows() - 1) if args[2] == 'pages' else 1)
        self.redraw()

    def xview(self, *args):
        total = max(1, self.edges[-1])
        if not args:
            return min(1, self.left_pixel / total), min(1, (self.left_pixel + self.viewport_width()) / total)
        if args[0] == 'moveto':
            self.left_pixel = round(float(args[1]) * total)
        else:
            self.left_pixel += int(args[1]) * (self.viewport_width() if args[2] == 'pages' else 30)
        self.redraw()

    def fitted(self, value, width):
        text = str(value).replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        if self.text_font.measure(text) <= width:
            return text
        low, high = 0, len(text)
        while low < high:
            mid = (low + high + 1) // 2
            if self.text_font.measure(text[:mid] + '…') <= width:
                low = mid
            else:
                high = mid - 1
        return text[:low] + '…'

    def redraw(self):
        self.clamp_offsets()
        self.delete('all')
        width, height = self.winfo_width(), self.winfo_height()
        rh, hh, gutter = self.row_height, self.header_height, self.gutter
        first_col = max(0, bisect_right(self.edges, self.left_pixel) - 1)
        last_col = min(len(self.headers), bisect_right(self.edges, self.left_pixel + self.viewport_width()))
        last_row = self.top_row + math.ceil(max(0, height - hh) / rh)
        r1, c1, r2, c2 = self.selection
        left = max(gutter, gutter + self.edges[c1] - self.left_pixel)
        right = min(width, gutter + self.edges[c2 + 1] - self.left_pixel)
        top = max(hh, hh + (r1 - self.top_row) * rh)
        bottom = min(height, hh + (r2 + 1 - self.top_row) * rh)
        selected_visible = right > left and bottom > top
        if selected_visible:
            self.create_rectangle(left, top, right, bottom, fill='#e1edf8', outline='')
        bounds = self.bbox(str(self.active[0]), str(self.active[1]))
        if bounds:
            x, y, w, h = bounds
            self.create_rectangle(x, y, x + w, y + h, fill='white', outline='')
        # Células vazias continuam a grade; somente colunas existentes têm cabeçalhos.
        for row in range(self.top_row, last_row):
            y = hh + (row - self.top_row) * rh
            for col in range(first_col, last_col):
                if row < len(self.rows):
                    value = self.rows[row][col]
                    x = gutter + self.edges[col + 1] - self.left_pixel - 7
                    self.create_text(x, y + rh / 2, anchor='e', text=self.fitted(value, self.column_widths[col] - 14),
                                     fill='#202020', font=self.text_font)
            self.create_line(gutter, y, width, y, fill='#d3d6da')
        for col in range(first_col, last_col + 1):
            x = gutter + self.edges[col] - self.left_pixel
            self.create_line(x, hh, x, height, fill='#d3d6da')
        x = gutter + self.edges[-1] - self.left_pixel
        while x < width:
            x += self.column_width
            self.create_line(x, hh, x, height, fill='#d3d6da')
        self.create_rectangle(0, 0, width, hh, fill='#eef0f3', outline='')
        for col in range(first_col, last_col):
            x, cw = gutter + self.edges[col] - self.left_pixel, self.column_widths[col]
            active = c1 <= col <= c2
            if active:
                self.create_rectangle(x, 0, x + cw, hh, fill='#dce9f5', outline='')
            self.create_text(x + cw / 2, 12, text=f'C{col + 1}', font=self.header_font, fill='#303b48')
            self.create_text(x + cw / 2, 36, text=self.fitted(self.headers[col], cw - 12), font=self.text_font, fill='#202020')
            self.create_line(x + cw, 0, x + cw, hh, fill='#bdc3ca')
        self.create_line(0, 24, width, 24, fill='#c8cdd3')
        self.create_line(0, hh, width, hh, fill='#aeb7c2')
        self.create_rectangle(0, 0, gutter, height, fill='#eef0f3', outline='')
        self.create_text(gutter / 2, hh / 2, text='↳', fill='#677482', font=self.header_font)
        for row in range(self.top_row, last_row):
            y = hh + (row - self.top_row) * rh
            if r1 <= row <= r2:
                self.create_rectangle(0, y, gutter, y + rh, fill='#dce9f5', outline='')
            self.create_text(gutter - 8, y + rh / 2, anchor='e', text=str(row + 1), fill='#4c5866', font=self.text_font)
            self.create_line(0, y, gutter, y, fill='#c8cdd3')
        self.create_line(gutter, 0, gutter, height, fill='#aeb7c2')
        if selected_visible:
            self.create_rectangle(left + 1, top + 1, right - 1, bottom - 1, outline='#246296', width=2)
        if bounds:
            x, y, w, h = bounds
            self.create_rectangle(x + 1, y + 1, x + w - 1, y + h - 1, outline='#246296', width=2)
        self.yset(*self.yview())
        self.xset(*self.xview())
