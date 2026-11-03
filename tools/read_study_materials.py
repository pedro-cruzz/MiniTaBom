"""Extrai evidências de leitura dos materiais; nunca grava nos originais."""
import hashlib
import json
from pathlib import Path
import zipfile

from openpyxl import load_workbook
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'docs' / 'analise_estudo'
XLSX = Path('C:/Users/pedro/Downloads/exercícios sistemas 2b.xlsx')
PDF = Path('C:/Users/pedro/Downloads/material de estatística 1 (1).pdf')


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    wb = load_workbook(XLSX, read_only=True, data_only=False, keep_links=False)
    records, lines = [], []
    for sheet in wb:
        cells = []
        lines.append(f'\n=== ABA {sheet.title!r} ({sheet.max_row} linhas, {sheet.max_column} colunas; {sheet.sheet_state}) ===')
        for row in sheet.iter_rows():
            entries = []
            for cell in row:
                if cell.value is not None:
                    cells.append(dict(cell=cell.coordinate, value=cell.value, type=cell.data_type))
                    entries.append(f'{cell.coordinate}: {cell.value}')
            if entries:
                lines.append(' | '.join(entries))
        records.append(dict(sheet=sheet.title, rows=sheet.max_row, columns=sheet.max_column,
                            state=sheet.sheet_state, cells=cells))
    with zipfile.ZipFile(XLSX) as archive:
        members = archive.namelist()
        media = [n for n in members if n.startswith('xl/media/')]
        drawings = [n for n in members if n.startswith('xl/drawings/') and n.endswith('.xml')]
        for name in drawings:
            lines.append('\n=== DRAWING ' + name + ' ===\n' + archive.read(name).decode('utf-8'))
    wb.close()
    (OUTPUT / 'excel_extraido.txt').write_text('\n'.join(lines), encoding='utf-8')
    (OUTPUT / 'excel_celulas.json').write_text(json.dumps(records, ensure_ascii=False, indent=2, default=str), encoding='utf-8')
    reader = PdfReader(PDF)
    pages = []
    for i, page in enumerate(reader.pages, 1):
        text = page.extract_text() or ''
        pages.append(dict(page=i, text=text, characters=len(text)))
    (OUTPUT / 'pdf_extraido.txt').write_text('\n\n'.join(f"=== PÁGINA {p['page']} ===\n{p['text']}" for p in pages), encoding='utf-8')
    (OUTPUT / 'pdf_paginas.json').write_text(json.dumps(pages, ensure_ascii=False, indent=2), encoding='utf-8')
    summary = dict(xlsx=dict(path=str(XLSX), sheets=[dict(sheet=r['sheet'], rows=r['rows'], columns=r['columns'],
                                                      populated=len(r['cells'])) for r in records], media=media),
                   pdf=dict(path=str(PDF), pages=len(pages), characters=[p['characters'] for p in pages]),
                   sha256={str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in (XLSX, PDF)})
    (OUTPUT / 'fontes.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=True, indent=2))


if __name__ == '__main__':
    main()
