"""Planilha Tkinter com edição na própria célula e navegação por teclado."""
import csv
import io
import tkinter as tk
from tkinter import ttk, messagebox
from sheet_grid import SheetGrid


def paste_block(rows, width, start, text):
    """Valida o bloco inteiro antes de modificar a planilha."""
    block = list(csv.reader(io.StringIO(text), delimiter='\t'))
    if not block:
        return False
    row, column = start
    if row < 0 or column < 0 or any(column + len(line) > width for line in block):
        raise ValueError('O bloco ultrapassa as colunas disponíveis. Adicione colunas antes de colar.')
    changed = False
    for offset, line in enumerate(block):
        target = row + offset
        while len(rows) <= target:
            rows.append([''] * width)
            changed = True
        for j, value in enumerate(line, column):
            if rows[target][j] != value:
                rows[target][j] = value
                changed = True
    return changed


def copy_block(rows, bounds):
    """TSV com aspas para preservar tabulações e quebras de linha nas células."""
    first_row, first_col, last_row, last_col = bounds
    output = io.StringIO(newline='')
    writer = csv.writer(output, delimiter='\t', lineterminator='\r\n')
    for row in range(first_row, last_row + 1):
        writer.writerow([rows[row][col] if row < len(rows) else ''
                         for col in range(first_col, last_col + 1)])
    # Uma célula simples mantém a convenção de copiar somente seu texto.
    return output.getvalue()[:-2]


def clear_block(rows, bounds):
    first_row, first_col, last_row, last_col = bounds
    changed = False
    for row in range(first_row, min(last_row + 1, len(rows))):
        for col in range(first_col, last_col + 1):
            if rows[row][col] != '':
                rows[row][col] = ''
                changed = True
    return changed


class Worksheet(ttk.Frame):
    def __init__(self, parent, on_change, on_select, on_rename):
        super().__init__(parent)
        self.on_change, self.on_select, self.on_rename = on_change, on_select, on_rename
        self.headers, self.rows = [], []
        self.active = (0, 0)
        self.anchor = self.extent = self.active
        self.drag_mode = self.resizing = None
        self.editor = None
        self.pending_border = None
        self.table = SheetGrid(self)
        sy = ttk.Scrollbar(self, orient='vertical', command=self.scroll_y)
        sx = ttk.Scrollbar(self, orient='horizontal', command=self.scroll_x)
        self.table.yset, self.table.xset = sy.set, sx.set
        self.table.grid(row=0, column=0, sticky='nsew')
        sy.grid(row=0, column=1, sticky='ns')
        sx.grid(row=1, column=0, sticky='ew')
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.table.bind('<Button-1>', self.click)
        self.table.bind('<Double-1>', self.double_click)
        self.table.bind('<B1-Motion>', self.drag)
        self.table.bind('<ButtonRelease-1>', self.release)
        self.table.bind('<Motion>', self.pointer)
        self.table.bind('<Return>', lambda event: self.start_edit())
        self.table.bind('<F2>', lambda event: self.start_edit())
        self.table.bind('<KeyPress>', self.keypress)
        for key, delta in [('Up', (-1, 0)), ('Down', (1, 0)), ('Left', (0, -1)), ('Right', (0, 1))]:
            self.table.bind('<' + key + '>', lambda event, delta=delta: self.move(*delta))
            self.table.bind('<Shift-' + key + '>', lambda event, delta=delta: self.move(*delta, extend=True))
        self.table.bind('<Tab>', lambda event: self.move_tab(1))
        self.table.bind('<Shift-Tab>', lambda event: self.move_tab(-1))
        self.table.bind('<Control-c>', self.copy)
        self.table.bind('<Control-v>', self.paste)
        self.table.bind('<Control-a>', self.select_all)
        self.table.bind('<Delete>', self.clear_selection)
        self.table.bind('<Control-Home>', lambda event: self.go_to_edge(False))
        self.table.bind('<Control-End>', lambda event: self.go_to_edge(True))
        self.table.bind('<MouseWheel>', self.mousewheel)
        self.table.bind('<Shift-MouseWheel>', self.mousewheel_horizontal)
        self.table.bind('<Configure>', self.viewport_changed)
        self.table.bind('<Control-z>', lambda event: self.winfo_toplevel().restore_history('undo'))
        self.table.bind('<Control-y>', lambda event: self.winfo_toplevel().restore_history('redo'))

    def set_data(self, headers, rows):
        self.cancel_edit()
        self.headers, self.rows = headers, rows
        self.active = (0, 0)
        self.render()

    def render(self):
        self.table.headers, self.table.rows = self.headers, self.rows
        self.table.sync_columns()
        self.select(*self.active)

    @property
    def selection_bounds(self):
        return (min(self.anchor[0], self.extent[0]), min(self.anchor[1], self.extent[1]),
                max(self.anchor[0], self.extent[0]), max(self.anchor[1], self.extent[1]))

    def select(self, row, column, extend=False):
        row, column = max(0, row), max(0, min(column, len(self.headers) - 1))
        self.active = (row, column)
        if not extend:
            self.anchor = self.active
        self.extent = self.active
        self.update_selection()

    def select_block(self, first, last, active=None):
        self.anchor, self.extent = first, last
        self.active = active or first
        self.update_selection()

    def update_selection(self):
        row, column = self.active
        self.table.active = self.active
        self.table.selection = self.selection_bounds
        if self.table.winfo_width() > 1:
            self.table.reveal(row, column)
        self.on_select(row, column)
        self.schedule_border()

    def schedule_border(self):
        if self.pending_border is not None:
            self.after_cancel(self.pending_border)
        self.pending_border = self.after_idle(self.draw_active_cell)

    def destroy(self):
        if self.pending_border is not None:
            self.after_cancel(self.pending_border)
            self.pending_border = None
        super().destroy()

    def draw_active_cell(self):
        self.pending_border = None
        self.table.redraw()

    def mousewheel(self, event):
        self.scroll_y('scroll', -int(event.delta / 120) or (-1 if event.delta > 0 else 1), 'units')
        return 'break'

    def mousewheel_horizontal(self, event):
        self.scroll_x('scroll', -int(event.delta / 120) or (-1 if event.delta > 0 else 1), 'units')
        return 'break'

    def viewport_changed(self, event=None):
        self.commit_edit()
        self.schedule_border()

    def click(self, event):
        self.commit_edit()
        self.resizing = self.drag_mode = None
        item, col = self.table.identify_row(event.y), self.table.identify_column(event.x)
        heading = self.table.identify_region(event.x, event.y) == 'heading'
        boundary = self.table.column_boundary(event.x) if heading else None
        if boundary is not None:
            self.resizing = (boundary, event.x, self.table.column_widths[boundary])
            return 'break'
        extend = bool(getattr(event, 'state', 0) & 1)
        if heading and col and col != '#0':
            column = int(col[1:]) - 1
            first = self.anchor[1] if extend else column
            self.select_block((0, first), (max(0, len(self.rows) - 1), column), active=(0, column))
            self.drag_mode = ('columns', first)
            self.table.focus_set()
            return 'break'
        if item and col:
            column = int(col[1:]) - 1 if col and col != '#0' else self.active[1]
            if col == '#0':
                row = int(item)
                first = self.anchor[0] if extend else row
                self.select_block((first, 0), (row, len(self.headers) - 1), active=(row, column))
                self.drag_mode = ('rows', first)
            else:
                self.select(int(item), column, extend=extend)
                self.drag_mode = ('cells', None)
            self.table.focus_set()
            return 'break'

    def drag(self, event):
        if self.resizing is not None:
            column, start, width = self.resizing
            self.table.resize_column(column, width + event.x - start)
            return 'break'
        if self.drag_mode is None:
            return 'break'
        if event.y < self.table.header_height:
            self.table.yview('scroll', -1, 'units')
        elif event.y >= self.table.winfo_height():
            self.table.yview('scroll', 1, 'units')
        if event.x < self.table.gutter:
            self.table.xview('scroll', -1, 'units')
        elif event.x >= self.table.winfo_width():
            self.table.xview('scroll', 1, 'units')
        row = self.table.identify_row(max(self.table.header_height, min(event.y, self.table.winfo_height() - 1)))
        x = max(self.table.gutter, min(event.x, self.table.winfo_width() - 1))
        col = self.table.column_at(x)
        col = min(len(self.headers) - 1, col if col is not None else len(self.headers) - 1)
        mode, first = self.drag_mode
        if mode == 'columns':
            self.select_block((0, first), (max(0, len(self.rows) - 1), col), active=(0, col))
        elif row:
            row = int(row)
            if mode == 'rows':
                self.select_block((first, 0), (row, len(self.headers) - 1), active=(row, self.active[1]))
            else:
                self.select(row, col, extend=True)
        return 'break'

    def release(self, event=None):
        self.resizing = self.drag_mode = None
        return 'break'

    def pointer(self, event):
        separator = event.y < self.table.header_height and self.table.column_boundary(event.x) is not None
        self.table.configure(cursor='sb_h_double_arrow' if separator else '')

    def double_click(self, event):
        col = self.table.identify_column(event.x)
        if self.table.identify_region(event.x, event.y) == 'heading':
            boundary = self.table.column_boundary(event.x)
            if boundary is not None:
                self.release()
                self.table.fit_column(boundary)
            elif col and col != '#0':
                self.release()
                self.on_rename(int(col[1:]) - 1)
            return 'break'
        item = self.table.identify_row(event.y)
        if item and col and col != '#0':
            self.select(int(item), int(col[1:]) - 1)
            return self.start_edit()

    def start_edit(self, initial=None):
        self.commit_edit()
        row, column = self.active
        self.select(row, column)
        bounds = self.table.bbox(str(row), str(column))
        if not bounds:
            return 'break'
        value = self.rows[row][column] if row < len(self.rows) else ''
        self.editor = ttk.Entry(self.table, font=('Segoe UI', 9), justify='right')
        self.editor.place(x=bounds[0], y=bounds[1], width=bounds[2], height=bounds[3])
        self.editor.insert(0, value if initial is None else initial)
        self.editor.focus_set()
        if initial is None:
            self.editor.selection_range(0, 'end')
        self.editor.bind('<Return>', lambda event: self.finish_move(1, 0))
        self.editor.bind('<Tab>', lambda event: self.finish_tab(1))
        self.editor.bind('<Shift-Tab>', lambda event: self.finish_tab(-1))
        self.editor.bind('<Escape>', lambda event: self.cancel_edit())
        self.editor.bind('<FocusOut>', lambda event: self.commit_edit())
        return 'break'

    def commit_edit(self):
        if self.editor is None:
            return
        editor, self.editor = self.editor, None
        value = editor.get()
        editor.destroy()
        row, column = self.active
        before = self.rows[row][column] if row < len(self.rows) else ''
        if value != before:
            while len(self.rows) <= row:
                self.rows.append([''] * len(self.headers))
            self.rows[row][column] = value
            self.on_change()
        self.on_select(row, column)
        self.schedule_border()

    def cancel_edit(self):
        if self.editor is not None:
            editor, self.editor = self.editor, None
            editor.destroy()
            self.table.focus_set()
            self.schedule_border()
        return 'break'

    def move(self, dr, dc, extend=False):
        self.commit_edit()
        self.select(self.active[0] + dr, self.active[1] + dc, extend=extend)
        return 'break'

    def move_tab(self, direction):
        self.commit_edit()
        position = max(0, self.active[0] * len(self.headers) + self.active[1] + direction)
        self.select(*divmod(position, len(self.headers)))
        return 'break'

    def finish_move(self, dr, dc):
        self.move(dr, dc)
        self.start_edit()
        return 'break'

    def finish_tab(self, direction):
        self.commit_edit()
        self.move_tab(direction)
        self.start_edit()
        return 'break'

    def keypress(self, event):
        if event.char and event.char.isprintable() and not event.state & 0x0c:
            return self.start_edit(event.char)

    def copy(self, event=None):
        self.commit_edit()
        value = copy_block(self.rows, self.selection_bounds)
        self.clipboard_clear()
        self.clipboard_append(value)
        return 'break'

    def paste(self, event=None):
        self.commit_edit()
        try:
            start = self.selection_bounds[:2]
            if paste_block(self.rows, len(self.headers), start, self.clipboard_get()):
                self.render()
                self.select(*start)
                self.on_change()
        except (tk.TclError, csv.Error, ValueError) as error:
            messagebox.showerror('Não foi possível colar', str(error), parent=self)
        return 'break'

    def select_all(self, event=None):
        self.commit_edit()
        self.select_block((0, 0), (max(0, len(self.rows) - 1), len(self.headers) - 1))
        return 'break'

    def clear_selection(self, event=None):
        self.commit_edit()
        if clear_block(self.rows, self.selection_bounds):
            self.on_change()
            self.on_select(*self.active)
            self.schedule_border()
        return 'break'

    def go_to_edge(self, end):
        self.commit_edit()
        self.select(max(0, len(self.rows) - 1) if end else 0, len(self.headers) - 1 if end else 0)
        return 'break'

    def scroll_y(self, *args):
        self.commit_edit()
        self.table.yview(*args)
        self.schedule_border()

    def scroll_x(self, *args):
        self.commit_edit()
        self.table.xview(*args)
        self.schedule_border()
