"""Prepara o projeto inteiro antes da confirmação e da instalação pela UI."""
from pathlib import Path

from background_tasks import TaskContext
from history import WorksheetHistory
from workspace_model import new_document, new_sheet, active_sheet, validate_document


def prepare_excel_import(workbook, path, context=None):
    context = context or TaskContext()
    context.report(0., 'Preparando o projeto do Excel…')
    document = new_document()
    document['worksheets'] = []
    for index, item in enumerate(workbook['worksheets']):
        context.report(.65 * index / len(workbook['worksheets']), 'Preparando aba ' + item['name'])
        sheet = new_sheet(item['name'], item['headers'], item['rows'])
        sheet['metadata']['excel_import'] = item['metadata']
        document['worksheets'].append(sheet)
    document['active_worksheet_id'] = next(s['id'] for s in document['worksheets'] if s['name'] == workbook['active_name'])
    document['metadata']['excel_source'] = Path(path).name
    lines = ['EXCEL ABERTO — ' + Path(path).name,
             f"{len(document['worksheets'])} aba(s). Troque de aba pelo seletor acima da planilha.",
             'Todas as linhas foram mantidas, com colunas A, B, C...; nenhum intervalo precisa ser informado.']
    for item in workbook['worksheets']:
        if item['metadata']['uncached_formulas']:lines.append(item['name'] + ': ' + item['metadata']['note'])
    if any(item['metadata']['excel_state'] != 'visible' for item in workbook['worksheets']):
        lines.append('Abas ocultas do arquivo também foram incluídas no seletor.')
    document['output'] = '\n'.join(lines) + '\n'
    context.report(.7, 'Conferindo o projeto do Excel…')
    validate_document(document)
    context.report(.85, 'Preparando o histórico da planilha…')
    sheet = active_sheet(document)
    history = WorksheetHistory([c['name'] for c in sheet['columns']], sheet['rows'], columns=sheet['columns'])
    context.report(1., 'Excel pronto para abrir')
    return dict(document=document, history=history)
