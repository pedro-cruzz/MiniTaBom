"""Histórico em memória da planilha, independente dos resultados da sessão."""
from copy import deepcopy


class WorksheetHistory:
    def __init__(self, headers, rows, limit=50):
        self.limit = limit
        self.states = [deepcopy((headers, rows))]
        self.position = 0

    def record(self, headers, rows):
        state = (headers, rows)
        if state == self.states[self.position]:
            return
        self.states[self.position + 1:] = [deepcopy(state)]
        if len(self.states) > self.limit + 1:
            self.states.pop(0)
        self.position = len(self.states) - 1

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
