"""Leitor de valores OOXML .xlsx, sem executar fórmulas, macros ou links."""
import posixpath
from pathlib import Path
import re
import zipfile
import xml.etree.ElementTree as ET

from data_operations import MAX_ROWS,MAX_COLUMNS,MAX_CELLS

NS={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
    'r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'p':'http://schemas.openxmlformats.org/package/2006/relationships'}


def _xml(archive,name):
    try:
        info=archive.getinfo(name)
        if info.file_size>64*1024**2:raise ValueError('Uma parte do Excel excede 64 MB.')
        return ET.fromstring(archive.read(name))
    except (KeyError,ET.ParseError) as error:raise ValueError('Estrutura Excel inválida ou não suportada: '+name) from error


def _open(path):
    try:archive=zipfile.ZipFile(path)
    except (OSError,zipfile.BadZipFile) as error:raise ValueError('Não foi possível abrir um arquivo .xlsx válido.') from error
    if len(archive.infolist())>10000 or sum(i.file_size for i in archive.infolist())>256*1024**2:
        archive.close();raise ValueError('Arquivo Excel excede os limites de leitura (256 MB descompactados).')
    return archive


def _sheets(archive):
    workbook=_xml(archive,'xl/workbook.xml');relationships=_xml(archive,'xl/_rels/workbook.xml.rels')
    targets={r.get('Id'):r.get('Target') for r in relationships if r.get('TargetMode')!='External'
             and r.get('Type','').endswith('/worksheet')}
    result=[]
    for sheet in workbook.findall('m:sheets/m:sheet',NS):
        target=targets.get(sheet.get('{'+NS['r']+'}id'))
        if not target:continue
        name=posixpath.normpath(target.lstrip('/') if target.startswith('/') else posixpath.join('xl',target))
        if not name.startswith('xl/') or '..' in name.split('/'):raise ValueError('Caminho de planilha inválido.')
        result.append(dict(name=sheet.get('name'),member=name,state=sheet.get('state','visible')))
    if not result:raise ValueError('Não há planilhas de células compatíveis no arquivo.')
    return result


def excel_sheets(path):
    with _open(path) as archive:return _sheets(archive)


def _coordinate(reference):
    match=re.fullmatch(r'\$?([A-Za-z]{1,3})\$?([1-9]\d*)',reference.strip())
    if not match:raise ValueError('Use intervalo no formato A1:B20.')
    column=0
    for char in match[1].upper():column=column*26+ord(char)-64
    row=int(match[2])
    if row>1048576 or column>16384:raise ValueError('Endereço fora dos limites do Excel.')
    return row,column


def read_excel(path,sheet_name,cell_range='',header=True):
    with _open(path) as archive:
        sheet=next((s for s in _sheets(archive) if s['name']==sheet_name),None)
        if sheet is None:raise ValueError('Selecione uma aba existente.')
        shared=[]
        if 'xl/sharedStrings.xml' in archive.namelist():
            shared=[''.join(t.text or '' for t in item.iter('{'+NS['m']+'}t')) for item in _xml(archive,'xl/sharedStrings.xml')]
        cells={};formulas=set()
        for cell in _xml(archive,sheet['member']).iter('{'+NS['m']+'}c'):
            coordinate=_coordinate(cell.get('r',''))
            value=cell.find('m:v',NS);kind=cell.get('t','n')
            if cell.find('m:f',NS) is not None:
                formulas.add(coordinate)
                if value is None or value.text is None:
                    cells[coordinate]=None;continue
            if kind=='inlineStr':text=''.join(t.text or '' for t in cell.iter('{'+NS['m']+'}t'))
            elif value is None:continue
            elif kind=='s':
                try:
                    index=int(value.text)
                    if not 0<=index<len(shared):raise IndexError
                    text=shared[index]
                except (ValueError,IndexError,TypeError):raise ValueError('Índice de texto inválido no Excel.') from None
            elif kind=='b':text='TRUE' if value.text=='1' else 'FALSE'
            elif kind=='e':text=value.text or '#ERRO'
            else:text=value.text or ''
            if text!='':cells[coordinate]=text
        if not cells:raise ValueError('A aba não contém valores para importar.')
        if cell_range.strip():
            references=cell_range.split(':')
            if len(references)>2:raise ValueError('Use um único intervalo retangular.')
            start=_coordinate(references[0]);end=_coordinate(references[-1])
        else:
            start=(min(r for r,c in cells),min(c for r,c in cells))
            end=(max(r for r,c in cells),max(c for r,c in cells))
        r1,c1=start;r2,c2=end
        height,width=r2-r1+1,c2-c1+1
        if not 1<=height<=MAX_ROWS or not 1<=width<=MAX_COLUMNS or height*width>MAX_CELLS:
            raise ValueError('Selecione intervalo com até 200000 linhas, 512 colunas e 2000000 células.')
        values=[];formula_count=0
        for r in range(r1,r2+1):
            row=[]
            for c in range(c1,c2+1):
                value=cells.get((r,c),'')
                if value is None:raise ValueError('Há fórmula sem resultado salvo no intervalo. Recalcule e salve no Excel antes de importar.')
                formula_count+=(r,c) in formulas;row.append(value)
            values.append(row)
        headers=[v.strip() for v in values.pop(0)] if header else [f'C{i+1}' for i in range(width)]
        if not all(headers) or len(set(headers))!=len(headers):
            raise ValueError('Os cabeçalhos do intervalo devem ser únicos e não vazios; escolha outro intervalo ou desmarque o cabeçalho.')
        # Serial numérico do Excel é preservado; tipo de coluna ainda é textual.
        return headers,values,dict(sheet=sheet_name,range=cell_range or 'área preenchida',formulas=formula_count,
                                   note='Datas numéricas do Excel permanecem como números seriais; fórmulas usam o último resultado salvo.')
