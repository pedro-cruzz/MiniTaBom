"""Mede tarefas e pulso Tk com dados sintéticos; sem abrir arquivos pessoais."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import platform
import sys
import tempfile
import time
import tracemalloc
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))


def measure(app, start):
    beats = [time.perf_counter()]
    after_id = [None]
    def heartbeat():
        beats.append(time.perf_counter())
        after_id[0] = app.after(10, heartbeat)
    after_id[0] = app.after(10, heartbeat)
    tracemalloc.start()
    begin = time.perf_counter()
    assert start()
    start_seconds = time.perf_counter() - begin
    worker = app._task_window.task
    deadline = begin + 60
    while app._task_window is not None:
        app.update()
        if time.perf_counter() > deadline:raise RuntimeError('Benchmark excedeu 60 segundos.')
        time.sleep(.001)
    end = time.perf_counter()
    app.after_cancel(after_id[0])
    beats.append(end)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return dict(start_seconds=start_seconds, total_seconds=end-begin,
                main_loop_beats=len(beats)-2, max_main_loop_gap_seconds=max(b-a for a,b in zip(beats, beats[1:])),
                python_traced_current_bytes=current, python_traced_peak_bytes=peak,
                outcome=worker.snapshot()['state'])


def write_book(path, row_count):
    ns = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('xl/workbook.xml', f'<workbook xmlns="{ns}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>' +
                         ''.join(f'<sheet name="Dados {i}" sheetId="{i}" r:id="r{i}"/>' for i in (1, 2)) + '</sheets></workbook>')
        archive.writestr('xl/_rels/workbook.xml.rels', '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' +
                         ''.join(f'<Relationship Id="r{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i}.xml"/>' for i in (1, 2)) + '</Relationships>')
        rows = ''.join(f'<row r="{i}">' + ''.join(f'<c r="{column}{i}"><v>{i+j}</v></c>' for j,column in enumerate('ABC')) + '</row>'
                       for i in range(1, row_count+1))
        for i in (1, 2):archive.writestr(f'xl/worksheets/sheet{i}.xml', f'<worksheet xmlns="{ns}"><sheetData>{rows}</sheetData></worksheet>')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    from app import MiniTaBom
    from inference import scientific_stats
    scientific_stats()
    app = MiniTaBom(); app.withdraw()
    try:
        generation = measure(app, lambda: app.start_random('Normal', {'mean': 0., 'sd': 1.}, row_count=10000, column_count=3, seed=2026))
        assert len(app.rows) == 10000 and len(app.document['analyses']) == 1
        app.sync_document(); before = deepcopy(app.document)
        def start_cancelled():
            accepted = app.start_random('Normal', {'mean': 0., 'sd': 1.}, row_count=100000, column_count=4, seed=1)
            app.after(20, app._task_window.cancel)
            return accepted
        cancellation = measure(app, start_cancelled)
        app.sync_document(); assert app.document == before
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'synthetic.xlsx'; write_book(path, 10000)
            app.dirty = False
            excel = measure(app, lambda: app.start_excel_import(path))
            assert len(app.document['worksheets']) == 2 and all(len(sheet['rows']) == 10000 for sheet in app.document['worksheets'])
        result = dict(python=platform.python_version(), generation=dict(rows=10000, new_columns=3, **generation),
                      cancellation=dict(request_after_ms=20, rows=100000, new_columns=4, document_preserved=True, **cancellation),
                      excel=dict(sheets=2, rows_per_sheet=10000, columns=3, **excel),
                      limitations=['Bibliotecas aquecidas, Tk oculto, tracemalloc ativo; não mede toda a memória nativa.',
                                   'O maior intervalo do pulso inclui a aplicação final síncrona e a medição; não extrapolar para o tamanho máximo.',
                                   'Cancelamento é cooperativo; uma chamada nativa em curso precisa retornar antes do próximo checkpoint.'])
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        print(json.dumps(result, ensure_ascii=False, indent=2))
    finally:
        app.destroy()


if __name__ == '__main__':main()
