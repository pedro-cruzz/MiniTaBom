"""Leitor de valores OOXML .xlsx, sem executar fórmulas, macros ou links."""
import posixpath
from pathlib import Path
import re
import zipfile
import xml.etree.ElementTree as ET

from data_operations import MAX_ROWS,MAX_COLUMNS,MAX_CELLS
from background_tasks import TaskContext

NS={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
    'r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'p':'http://schemas.openxmlformats.org/package/2006/relationships'}


def _xml(archive,name,context=None):
    context = context or TaskContext()
    try:
        info=archive.getinfo(name)
        if info.file_size>64*1024**2:raise ValueError('Uma parte do Excel excede 64 MB.')
        parser = ET.XMLParser()
        read = 0
        with archive.open(name) as source:
            while True:
                context.checkpoint()
                chunk = source.read(65536)
                if not chunk:break
                parser.feed(chunk)
                read += len(chunk)
                context.report(min(1., read / max(1, info.file_size)), 'Lendo dados do Excel…')
        root = parser.close()
        context.checkpoint()
        return root
    except (KeyError,ET.ParseError,zipfile.BadZipFile,EOFError,RuntimeError) as error:raise ValueError('Estrutura Excel inválida ou não suportada: '+name) from error


def _open(path):
    try:archive=zipfile.ZipFile(path)
    except (OSError,zipfile.BadZipFile) as error:raise ValueError('Não foi possível abrir um arquivo .xlsx válido.') from error
    if len(archive.infolist())>10000 or sum(i.file_size for i in archive.infolist())>256*1024**2:
        archive.close();raise ValueError('Arquivo Excel excede os limites de leitura (256 MB descompactados).')
    return archive


def _sheets(archive,context=None):
    context = context or TaskContext()
    workbook=_xml(archive,'xl/workbook.xml',context.phase(0.,.5));relationships=_xml(archive,'xl/_rels/workbook.xml.rels',context.phase(.5,1.))
    targets={r.get('Id'):r.get('Target') for r in relationships if r.get('TargetMode')!='External'
             and r.get('Type','').endswith('/worksheet')}
    result=[]
    for sheet in workbook.findall('m:sheets/m:sheet',NS):
        context.checkpoint()
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


def _shared_strings(archive,context=None):
    context = context or TaskContext()
    if 'xl/sharedStrings.xml' not in archive.namelist():return []
    root = _xml(archive,'xl/sharedStrings.xml',context.phase(0.,.5))
    result = []
    for index,item in enumerate(root):
        if index % 1024 == 0:context.report(.5 + .5 * index / max(1,len(root)), 'Lendo os textos do Excel…')
        result.append(''.join(t.text or '' for t in item.iter('{'+NS['m']+'}t')))
    context.report(1., 'Textos do Excel preparados')
    return result


def _sheet_cells(archive,sheet,shared,context=None):
    context = context or TaskContext()
    cells={};formulas={}
    root = _xml(archive,sheet['member'],context.phase(0.,.45))
    source_cells = list(root.iter('{'+NS['m']+'}c'))
    for index,cell in enumerate(source_cells):
        if index % 1024 == 0:
            context.report(.45 + .55 * index / max(1,len(source_cells)), 'Lendo células da aba ' + sheet['name'])
        coordinate=_coordinate(cell.get('r',''))
        value=cell.find('m:v',NS);kind=cell.get('t','n');formula=cell.find('m:f',NS)
        if formula is not None:
            formulas[coordinate]='='+formula.text if formula.text else '#FORMULA SEM RESULTADO SALVO'
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
    context.report(1., 'Células lidas: ' + sheet['name'])
    return cells,formulas


def column_letter(number):
    text=''
    while number:
        number,remainder=divmod(number-1,26);text=chr(65+remainder)+text
    return text


def _table(cells,formulas,sheet_name,cell_range='',header=True,automatic=False,context=None):
    context = context or TaskContext()
    context.checkpoint()
    if not cells:
        if automatic:return ['A','B','C'],[],dict(sheet=sheet_name,range='vazia',formulas=0,uncached_formulas=0,note='Aba vazia.')
        raise ValueError('A aba não contém valores para importar.')
    if cell_range.strip():
        references=cell_range.split(':')
        if len(references)>2:raise ValueError('Use um único intervalo retangular.')
        start=_coordinate(references[0]);end=_coordinate(references[-1])
    else:
        rmin,cmin,rmax,cmax=1048576,16384,1,1
        for index,(r,c) in enumerate(cells):
            if index % 4096 == 0:context.checkpoint()
            rmin,cmin,rmax,cmax=min(rmin,r),min(cmin,c),max(rmax,r),max(cmax,c)
        start=(1,1) if automatic else (rmin,cmin)
        end=(rmax,cmax)
    r1,c1=start;r2,c2=end
    height,width=r2-r1+1,c2-c1+1
    if not 1<=height<=MAX_ROWS or not 1<=width<=MAX_COLUMNS or height*width>MAX_CELLS:
        raise ValueError(('A aba excede o tamanho suportado: ' if automatic else 'Selecione intervalo com até ')+
                         '200000 linhas, 512 colunas e 2000000 células.')
    values=[];formula_count=uncached=0
    for r in range(r1,r2+1):
        context.checkpoint()
        if (r-r1) % 256 == 0:context.report((r-r1)/height, 'Preparando linhas da aba ' + sheet_name)
        row=[]
        for c in range(c1,c2+1):
            value=cells.get((r,c),'')
            if value is None:
                if not automatic:raise ValueError('Há fórmula sem resultado salvo no intervalo. Recalcule e salve no Excel antes de importar.')
                value=formulas[(r,c)];uncached+=1
            formula_count+=(r,c) in formulas;row.append(value)
        values.append(row)
    headers=([column_letter(c) for c in range(c1,c2+1)] if automatic else
             [v.strip() for v in values.pop(0)] if header else [f'C{i+1}' for i in range(width)])
    if not all(headers) or len(set(headers))!=len(headers):
        raise ValueError('Os cabeçalhos do intervalo devem ser únicos e não vazios; escolha outro intervalo ou desmarque o cabeçalho.')
    note='Datas numéricas do Excel permanecem como números seriais; fórmulas usam o último resultado salvo.'
    if uncached:note+=f' {uncached} fórmula(s) sem resultado salvo exibidas como texto, sem cálculo.'
    context.report(1., 'Aba preparada: ' + sheet_name)
    return headers,values,dict(sheet=sheet_name,range=cell_range or ('A1:'+column_letter(c2)+str(r2) if automatic else 'área preenchida'),
                              formulas=formula_count,uncached_formulas=uncached,note=note)


def read_excel(path,sheet_name,cell_range='',header=True):
    with _open(path) as archive:
        sheet=next((s for s in _sheets(archive) if s['name']==sheet_name),None)
        if sheet is None:raise ValueError('Selecione uma aba existente.')
        cells,formulas=_sheet_cells(archive,sheet,_shared_strings(archive))
        return _table(cells,formulas,sheet_name,cell_range,header)


def read_excel_workbook(path,context=None):
    """Abre todas as abas sem pedir intervalo e sem descartar a primeira linha."""
    context = context or TaskContext()
    context.report(0., 'Abrindo Excel…')
    with _open(path) as archive:
        sheets=_sheets(archive,context.phase(0.,.04));names=[s['name'] for s in sheets]
        if (len(sheets)>100 or any(not isinstance(n,str) or not n.strip() for n in names) or len(set(names))!=len(names)):
            raise ValueError('Use até 100 abas com nomes únicos e não vazios.')
        shared=_shared_strings(archive,context.phase(.04,.14));result=[];total_cells=0
        # Peso por bytes descompactados para não tratar abas desiguais como iguais.
        try:weights=[max(1,archive.getinfo(sheet['member']).file_size) for sheet in sheets]
        except KeyError as error:raise ValueError('O arquivo Excel referencia uma aba ausente.') from error
        total_weight=sum(weights);done_weight=0
        for sheet,weight in zip(sheets,weights):
            phase=context.phase(.14+.82*done_weight/total_weight,.14+.82*(done_weight+weight)/total_weight)
            cells,formulas=_sheet_cells(archive,sheet,shared,phase.phase(0.,.7))
            headers,rows,meta=_table(cells,formulas,sheet['name'],automatic=True,context=phase.phase(.7,1.))
            total_cells+=len(headers)*len(rows)
            if total_cells>MAX_CELLS:raise ValueError('O conjunto de abas excede 2000000 células.')
            meta['excel_state']=sheet['state']
            result.append(dict(name=sheet['name'],headers=headers,rows=rows,metadata=meta))
            done_weight+=weight
        active=next((s['name'] for s in sheets if s['state']=='visible'),names[0])
        workbook=_xml(archive,'xl/workbook.xml',context.phase(.96,1.));view=workbook.find('m:bookViews/m:workbookView',NS)
        if view is not None:
            try:
                tabs=workbook.findall('m:sheets/m:sheet',NS);index=int(view.get('activeTab','0'))
                if not 0<=index<len(tabs):raise IndexError
                original=tabs[index].get('name')
                if any(s['name']==original and s['state']=='visible' for s in sheets):active=original
            except (ValueError,IndexError):pass
        context.report(1., 'Excel lido · preparando o projeto')
        return dict(worksheets=result,active_name=active)
