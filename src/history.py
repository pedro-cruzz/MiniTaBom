"""Histórico em memória da planilha, independente dos resultados da sessão."""
from copy import deepcopy


class WorksheetHistory:
    def __init__(self, headers, rows, limit=50, columns=None):
        self.limit = limit
        self.states = [deepcopy((headers, rows))]
        self.position = 0
        self.column_states = [deepcopy(columns)]

    def record(self, headers, rows, columns=None):
        state = (headers, rows)
        if state == self.states[self.position]:
            if columns is not None:
                self.column_states[self.position] = deepcopy(columns)
            return
        self.states[self.position + 1:] = [deepcopy(state)]
        self.column_states[self.position + 1:] = [deepcopy(columns)]
        if len(self.states) > self.limit + 1:
            self.states.pop(0)
            self.column_states.pop(0)
        self.position = len(self.states) - 1

    def attach_columns(self, headers, rows, columns):
        if (headers, rows) == self.states[self.position] and self.column_states[self.position] is None:
            self.column_states[self.position] = deepcopy(columns)

    def current_columns(self):
        return deepcopy(self.column_states[self.position])

    def undo(self):
        if self.position == 0:
            return None
        self.position -= 1
        return deepcopy(self.states[self.position])

    def redo(self):
        if self.position + 1 >= len(self.states):
            return None
        self.position += 1
        return deepcopy(self.states[self.position])
