from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from excel_import import read_excel_workbook,read_excel
from project import load_document


def write_book(path,formula=False):
    ns='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
    workbook=f'<workbook xmlns="{ns}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><bookViews><workbookView activeTab="1"/></bookViews><sheets><sheet name="Lista" sheetId="1" r:id="r1"/><sheet name="Dados" sheetId="2" r:id="r2"/><sheet name="Vazia" sheetId="3" state="hidden" r:id="r3"/></sheets></workbook>'
    rels='<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'+''.join(f'<Relationship Id="r{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i}.xml"/>' for i in (1,2,3))+'</Relationships>'
    first=f'<worksheet xmlns="{ns}"><dimension ref="A1:XFD1048576"/><sheetData><row r="1"><c r="A1" t="inlineStr"><is><t>Lista de exercícios</t></is></c></row><row r="4"><c r="B4" t="inlineStr"><is><t>Grupo</t></is></c><c r="C4" t="inlineStr"><is><t>Grupo</t></is></c></row><row r="5"><c r="B5"><v>1.5</v></c><c r="C5"><v>3</v></c></row><row r="1048576"><c r="XFD1048576" s="1"/></row></sheetData></worksheet>'
    second=f'<worksheet xmlns="{ns}"><sheetData><row r="1"><c r="A1" t="inlineStr"><is><t>Valor</t></is></c></row><row r="2"><c r="A2"><v>5</v></c><c r="B2">'+('<f>A2*2</f>' if formula else '<f>A2*2</f><v>10</v>')+'</c></row></sheetData></worksheet>'
    with zipfile.ZipFile(path,'w') as z:
        for name,text in [('xl/workbook.xml',workbook),('xl/_rels/workbook.xml.rels',rels),('xl/worksheets/sheet1.xml',first),('xl/worksheets/sheet2.xml',second),('xl/worksheets/sheet3.xml',f'<worksheet xmlns="{ns}"><sheetData/></worksheet>')]:z.writestr(name,text)


class ExcelOpenTests(unittest.TestCase):
    def test_all_sheets_coordinates_titles_duplicate_headers_and_blanks_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'book.xlsx';write_book(path)
            result=read_excel_workbook(path)
        self.assertEqual(result['active_name'],'Dados')
        self.assertEqual([s['name'] for s in result['worksheets']],['Lista','Dados','Vazia'])
        first=result['worksheets'][0];self.assertEqual(first['headers'],['A','B','C'])
        self.assertEqual(first['rows'][0],['Lista de exercícios','',''])
        self.assertEqual(first['rows'][3],['','Grupo','Grupo'])
        self.assertEqual(first['rows'][4],['','1.5','3'])
        self.assertEqual(first['metadata']['range'],'A1:C5')
        self.assertEqual(result['worksheets'][1]['rows'],[['Valor',''],['5','10']])
        self.assertEqual(result['worksheets'][2]['rows'],[])

    def test_uncached_formula_is_text_while_explicit_table_import_stays_strict(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'book.xlsx';write_book(path,True)
            result=read_excel_workbook(path)
            self.assertEqual(result['worksheets'][1]['rows'][1][1],'=A2*2')
            self.assertEqual(result['worksheets'][1]['metadata']['uncached_formulas'],1)
            with self.assertRaisesRegex(ValueError,'fórmula sem resultado'):read_excel(path,'Dados','A1:B2')


class ExcelOpenInterfaceTests(unittest.TestCase):
    def setUp(self):
        from app import MiniTaBom
        self.app=MiniTaBom();self.app.withdraw();self.addCleanup(self.app.destroy)

    def test_open_file_without_range_or_intermediate_dialog_and_save_all_tabs(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'book.xlsx';write_book(path)
            with patch('app.filedialog.askopenfilename',return_value=str(path)),patch('app.ExcelDialog',side_effect=AssertionError('must not ask for range')):
                self.assertTrue(self.app.open_excel())
            self.assertEqual(self.app.sheet_picker.get(),'Dados')
            self.assertEqual(self.app.rows,[['Valor',''],['5','10']])
            self.assertTrue(self.app.dirty)
            self.app.switch_worksheet(self.app.document['worksheets'][0]['id'])
            self.assertEqual(self.app.rows[4],['','1.5','3'])
            saved=Path(directory)/'book.statlab';self.app.project_path=str(saved);self.assertTrue(self.app.save_project())
            loaded=load_document(saved);self.assertEqual(len(loaded['worksheets']),3)
            self.assertEqual(loaded['worksheets'][0]['metadata']['excel_import']['range'],'A1:C5')

    def test_cancel_and_corrupt_workbook_preserve_the_current_project(self):
        before=deepcopy(self.app.document)
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'book.xlsx';write_book(path)
            with patch('app.filedialog.askopenfilename',return_value=str(path)),patch.object(self.app,'confirm_replace',return_value=False):
                self.assertFalse(self.app.open_excel())
            self.assertEqual(self.app.document,before)
            path.write_text('not an excel file',encoding='utf-8')
            with patch('app.filedialog.askopenfilename',return_value=str(path)),patch('app.messagebox.showerror'):
                self.assertIsNone(self.app.open_excel())
            self.assertEqual(self.app.document,before)

    def test_optional_header_promotion_preserves_ids_and_undo(self):
        from history import WorksheetHistory
        from workspace_model import active_sheet
        self.app.headers=['A','B'];self.app.rows=[['B','A'],['1','2'],['3','4']]
        self.app.history=WorksheetHistory(self.app.headers,self.app.rows);self.app.refresh()
        ids=[c['id'] for c in active_sheet(self.app.document)['columns']]
        self.assertTrue(self.app.promote_first_row());self.assertEqual(self.app.headers,['B','A'])
        self.assertEqual(self.app.rows,[['1','2'],['3','4']])
        self.assertEqual([c['id'] for c in active_sheet(self.app.document)['columns']],ids)
        self.app.undo_data();self.assertEqual(self.app.headers,['A','B'])
        self.assertEqual(self.app.rows[0],['B','A'])
