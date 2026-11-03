"""Prévia manual de desenvolvimento: registra geometria, sem automatizar entradas."""
import json
from pathlib import Path
import sys

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))
from app import MiniTaBom
from ui_geometry import monitor_work_area, centered_position


class ProbeLab(MiniTaBom):
    def center_dialog(self, dialog):
        dialog.update_idletasks()
        parent = (self.winfo_rootx(), self.winfo_rooty(), self.winfo_width(), self.winfo_height())
        size = getattr(dialog, 'initial_size', (dialog.winfo_width(), dialog.winfo_height()))
        area = monitor_work_area(self)
        record = dict(title=dialog.title(), parent=parent, size=size, work_area=area,
                      calculated=centered_position(parent, size, area), before=dialog.geometry())
        super().center_dialog(dialog)
        record['after'] = dialog.geometry()
        path = PROJECT / 'diagnosticos' / 'geometry_probe.json'
        path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps(record, indent=2), encoding='utf-8')


if __name__ == '__main__':
    app = ProbeLab()
    app.title('MiniTaBom — conferência de posicionamento')
    app.mainloop()
