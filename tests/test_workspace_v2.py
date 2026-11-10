from copy import deepcopy
import json
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from analysis_service import execute_t_one, rerun_analysis
from workspace_model import (new_document, new_sheet, active_sheet, sync_sheet,
                             validate_document, pack_numbers, unpack_numbers, is_stale)
from project import load_document, save_document, save_project, load_project


class WorkspaceV2Tests(unittest.TestCase):
    def sample(self):
        return new_document(['Valores','Texto'],[['0','ação'],['2',''],['*','ausente']], 'Sessão antiga\n')

    def test_migrate_v1_preserves_every_cell_and_output_then_ids_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'antigo.statlab'
            save_project(path,['A'],[['1,5'],['*'],['']], 'Relatório antigo\n')
            original=path.read_bytes()
            document=load_document(path)
            self.assertEqual(path.read_bytes(),original)
            self.assertEqual(document['metadata']['migration']['from_version'],1)
            target=Path(directory)/'novo.statlab';save_document(target,document)
            self.assertEqual(load_document(target),document)
            self.assertEqual(load_project(target),(['A'],[['1,5'],['*'],['']],'Relatório antigo\n'))

    def test_multiple_sheets_types_formats_and_active_identity_round_trip(self):
        document=self.sample();other=new_sheet('Outra',['Tempo'],[['2']])
        other['columns'][0].update(type='numeric',format={'decimals':2},metadata={'unit':'s'})
        document['worksheets'].append(other);document['active_worksheet_id']=other['id']
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'multi.statlab';save_document(path,document)
            self.assertEqual(load_document(path),document)
            self.assertEqual(load_project(path),(['Tempo'],[['2']],document['output']))

    def test_rename_and_reorder_preserve_variable_identity(self):
        sheet=active_sheet(self.sample());ids=[c['id'] for c in sheet['columns']]
        rows=deepcopy(sheet['rows'])
        self.assertTrue(sync_sheet(sheet,['Valor renomeado','Texto'],rows))
        self.assertEqual([c['id'] for c in sheet['columns']],ids)
        sync_sheet(sheet,['Texto','Valor renomeado'],[r[::-1] for r in rows])
        self.assertEqual([c['id'] for c in sheet['columns']],ids[::-1])
        revision=sheet['revision']
        self.assertFalse(sync_sheet(sheet,['Texto','Valor renomeado'],[r[::-1] for r in rows]))
        self.assertEqual(sheet['revision'],revision)

    def test_t_analytic_result_full_precision_defaults_and_missing(self):
        sheet=active_sheet(self.sample())
        result=execute_t_one(sheet,sheet['columns'][0]['id'])
        values=unpack_numbers(result['values'])
        self.assertAlmostEqual(values['p'],.5,places=12)  # t_1 = Cauchy, T=1
        self.assertEqual(values['df'],1)
        self.assertEqual(result['missing'],{'policy':'omit_empty_or_star','counts':[1]})
        self.assertEqual(result['parameters'],dict(null=0.,confidence=95.,alternative='two-sided',perform_test=True))
        self.assertEqual(result['source']['fingerprint'],sheet['fingerprint'])

    def test_result_round_trip_and_new_execution_preserves_previous(self):
        document=self.sample();sheet=active_sheet(document)
        result=execute_t_one(sheet,sheet['columns'][0]['id'],alternative='greater',null=1)
        document['analyses'].append(result)
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'analysis.statlab';save_document(path,document)
            loaded=load_document(path)
        self.assertEqual(loaded['analyses'],document['analyses'])
        self.assertEqual(unpack_numbers(loaded['analyses'][0]['values'])['high'],math.inf)
        before=deepcopy(loaded['analyses'][0]);source=active_sheet(loaded)
        sync_sheet(source,['Valores','Texto'],[['4','ação'],['6',''],['*','ausente']])
        self.assertTrue(is_stale(before,source))
        rerun=rerun_analysis(loaded,before['analysis_id']);loaded['analyses'].append(rerun)
        self.assertEqual(loaded['analyses'][0],before)
        self.assertEqual(rerun['parent_analysis_id'],before['analysis_id'])
        self.assertNotEqual(rerun['analysis_id'],before['analysis_id'])
        self.assertFalse(is_stale(rerun,source))
        self.assertGreater(unpack_numbers(rerun['values'])['estimate'],unpack_numbers(before['values'])['estimate'])
        validate_document(loaded)

    def test_rerun_resolves_column_id_after_reorder_and_rename(self):
        document=self.sample();sheet=active_sheet(document)
        old=execute_t_one(sheet,sheet['columns'][0]['id']);document['analyses'].append(old)
        sync_sheet(sheet,['Texto','Valores'],[r[::-1] for r in sheet['rows']])
        sync_sheet(sheet,['Texto','Novo nome'],sheet['rows'])
        new=rerun_analysis(document,old['analysis_id'])
        self.assertEqual(new['values']['estimate'],old['values']['estimate'])
        self.assertEqual(new['values']['labels'],['Novo nome'])

    def test_missing_original_column_refuses_rerun_and_keeps_history(self):
        document=self.sample();sheet=active_sheet(document)
        document['analyses'].append(execute_t_one(sheet,sheet['columns'][0]['id']))
        sync_sheet(sheet,['Texto'],[[r[1]] for r in sheet['rows']])
        with self.assertRaises(ValueError):rerun_analysis(document,document['analyses'][0]['analysis_id'])
        self.assertEqual(len(document['analyses']),1)

    def test_numeric_tags_and_nan_refused(self):
        self.assertEqual(unpack_numbers(pack_numbers([math.inf,-math.inf,1.23456789123456])),[math.inf,-math.inf,1.23456789123456])
        with self.assertRaises(ValueError):pack_numbers(math.nan)
        with self.assertRaises(ValueError):unpack_numbers({'$statlab_number':'nan'})

    def test_invalid_documents_and_fingerprints(self):
        for mutate in (
            lambda d:d.update(active_worksheet_id='missing'),
            lambda d:d.update(version=True),
            lambda d:d.update(worksheets=[]),
            lambda d:d['worksheets'].append(deepcopy(d['worksheets'][0])),
            lambda d:d['worksheets'][0]['rows'][0].append('extra'),
            lambda d:d['worksheets'][0]['rows'][0].__setitem__(0,'changed'),
            lambda d:d['worksheets'][0]['columns'][0].update(type='code'),
            lambda d:d['metadata'].update(bad=math.nan),
        ):
            document=self.sample();mutate(document)
            with self.subTest(document=document),self.assertRaises(ValueError):validate_document(document)

    def test_failed_v2_replace_preserves_target_and_removes_temp(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'safe.statlab';save_document(path,self.sample());before=path.read_bytes()
            with patch('project.os.replace',side_effect=OSError('simulated')):
                with self.assertRaises(OSError):save_document(path,new_document())
            self.assertEqual(path.read_bytes(),before)
            self.assertEqual(list(Path(directory).iterdir()),[path])

    def test_duplicate_keys_nonfinite_literals_and_invalid_result_contract_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'invalid.statlab'
            for text in ('{"format":"statlab","format":"other"}', '{"x":NaN}', '{"x":Infinity}'):
                path.write_text(text,encoding='utf-8')
                with self.subTest(text=text),self.assertRaises(ValueError):load_document(path)
        document=self.sample();sheet=active_sheet(document)
        result=execute_t_one(sheet,sheet['columns'][0]['id']);document['analyses'].append(result)
        for change in (lambda r:r['parameters'].update(perform_test='yes'),
                       lambda r:r['parameters'].update(confidence=-1),
                       lambda r:r.update(parent_analysis_id=r['analysis_id'])):
            candidate=deepcopy(document);change(candidate['analyses'][0])
            with self.assertRaises(ValueError):validate_document(candidate)

    def test_registry_ids_and_files(self):
        root=Path(__file__).resolve().parents[1]
        registry=json.loads((root/'CAPACIDADES.json').read_text(encoding='utf-8'))
        self.assertFalse(registry['parity_validated']);self.assertFalse(registry['inventory_exhaustive'])
        ids=[r['id'] for r in registry['requirements']];self.assertEqual(len(ids),len(set(ids)))
        for requirement in registry['requirements']:
            self.assertEqual(requirement['states']['validation16'],'pending')
            if requirement['kind']=='requirement':
                for path in requirement['files']+requirement['tests']:
                    self.assertTrue((root/path).is_file(),path)


class WorkspaceInterfaceTests(unittest.TestCase):
    def setUp(self):
        from app import MiniTaBom
        self.app=MiniTaBom();self.app.withdraw();self.addCleanup(self.app.destroy)
        self.app.headers=['X'];self.app.rows=[['0'],['2'],['*']];self.app.refresh()

    def test_two_worksheets_analyze_save_reopen_rerun_and_export(self):
        self.assertTrue(self.app.run_ttest('one',0))
        first=self.app.document['active_worksheet_id']
        self.assertTrue(self.app.add_worksheet('Segunda'))
        self.app.headers=['Y'];self.app.rows=[['4'],['6']];self.app.data_changed();self.app.refresh()
        self.assertTrue(self.app.run_ttest('one',0,null=5,confidence=90))
        second=self.app.document['active_worksheet_id']
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'duas.statlab';self.app.project_path=str(path)
            self.assertTrue(self.app.save_project())
            with patch('app.filedialog.askopenfilename',return_value=str(path)):
                self.app.open_project()
            self.assertEqual(self.app.document['active_worksheet_id'],second)
            self.assertEqual(len(self.app.document['worksheets']),2)
            self.assertEqual(len(self.app.document['analyses']),2)
            self.app.switch_worksheet(first)
            self.assertEqual(self.app.rows,[['0'],['2'],['*']])
            self.app.rows[0][0]='4';self.app.data_changed()
            old=deepcopy(self.app.document['analyses'][0])
            self.assertTrue(self.app.rerun_saved_analysis(old['analysis_id']))
            self.assertEqual(old,self.app.document['analyses'][0])
            history=self.app.analysis_history_dialog()
            history.tree.selection_set(old['analysis_id'])
            self.assertEqual(history.tree.item(old['analysis_id'],'values')[-1],'Dados alterados')
            export=Path(directory)/'resultado.json'
            with patch('analysis_history_dialog.filedialog.asksaveasfilename',return_value=str(export)):
                history.export()
            self.assertEqual(json.loads(export.read_text(encoding='utf-8')),old)
            history.destroy()

    def test_undo_history_is_independent_between_sheets(self):
        from history import WorksheetHistory
        self.app.history=WorksheetHistory(self.app.headers,self.app.rows)
        first=self.app.document['active_worksheet_id']
        self.app.rows[0][0]='10';self.app.data_changed()
        self.app.add_worksheet('B');second=self.app.document['active_worksheet_id']
        self.app.add_row();self.assertEqual(len(self.app.rows),1)
        self.app.switch_worksheet(first);self.app.undo_data();self.assertEqual(self.app.rows[0][0],'0')
        self.app.switch_worksheet(second);self.assertEqual(len(self.app.rows),1)
        self.app.undo_data();self.assertEqual(self.app.rows,[])

    def test_invalid_open_and_analysis_do_not_replace_project(self):
        before=deepcopy(self.app.document)
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'bad.statlab';path.write_text('{"format":"statlab","version":2}',encoding='utf-8')
            with patch('app.filedialog.askopenfilename',return_value=str(path)),patch('app.messagebox.showerror'):
                self.app.open_project()
            self.assertEqual(self.app.document,before)
        with patch('app.messagebox.showerror'):
            self.assertFalse(self.app.run_ttest('one',0,confidence=100))
        self.assertEqual(self.app.document['analyses'],[])

    def test_new_project_and_csv_import_reset_old_structured_history(self):
        self.app.run_ttest('one',0);self.app.add_worksheet('Outra')
        with patch.object(self.app,'confirm_replace',return_value=True):self.app.new_project()
        self.assertEqual(len(self.app.document['worksheets']),1)
        self.assertEqual(self.app.document['analyses'],[])
        self.assertEqual(self.app.rows,[])
