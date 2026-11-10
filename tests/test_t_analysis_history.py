from copy import deepcopy
import json
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from analysis_service import execute_t, rerun_analysis
from workspace_model import new_document, active_sheet, sync_sheet, is_stale, validate_document
from project import save_document, load_document


class TAnalysisHistoryTests(unittest.TestCase):
    def test_history_metadata_limit_branch_and_snapshot_isolation(self):
        from history import WorksheetHistory
        columns=[dict(id='original',name='A',metadata={'unit':'s'})]
        history=WorksheetHistory(['A'],[['0']],limit=2,columns=columns)
        for value in ('1','2','3'):
            history.record(['A'],[[value]],columns=columns)
        self.assertEqual(len(history.states),3);self.assertEqual(len(history.column_states),3)
        columns[0]['metadata']['unit']='mutated'
        self.assertEqual(history.current_columns()[0]['metadata']['unit'],'s')
        history.undo();history.record(['A'],[['branch']],columns=[dict(id='branch')])
        self.assertIsNone(history.redo());self.assertEqual(history.current_columns()[0]['id'],'branch')

    def document(self):
        return new_document(['A','B','Resposta','Grupo'],
                            [['0','2','0','A'],['2','4','2','A'],['*','','2','B'],['','','4','B']])

    def run_record(self, document, mode, indices=(), **options):
        sheet=active_sheet(document)
        record=execute_t(sheet,mode,[sheet['columns'][i]['id'] for i in indices],**options)
        document['analyses'].append(record)
        return record

    def test_all_seven_formats_round_trip_and_rerun(self):
        for mode,source,indices,summaries in (
            ('one','columns',[0],None),('one','summary',[],[dict(n=2,mean=1.,sd=math.sqrt(2))]),
            ('paired','columns',[0,1],None),('paired','summary',[],[dict(n=3,mean=-2.,sd=1.)]),
            ('two','columns',[0,1],None),('two','stacked',[2,3],None),
            ('two','summary',[],[dict(n=2,mean=1.,sd=math.sqrt(2)),dict(n=2,mean=3.,sd=math.sqrt(2))])):
            # Raw paired differences must have nonzero dispersion.
            document=self.document();sheet=active_sheet(document)
            if mode=='paired' and source=='columns':
                rows=deepcopy(sheet['rows']);rows[0][1]='0';sync_sheet(sheet,['A','B','Resposta','Grupo'],rows)
            with self.subTest(mode=mode,source=source):
                old=self.run_record(document,mode,indices,source=source,summaries=summaries,alternative='less')
                snapshot=deepcopy(old)
                with tempfile.TemporaryDirectory() as directory:
                    path=Path(directory)/'t.statlab';save_document(path,document);loaded=load_document(path)
                result=rerun_analysis(loaded,old['analysis_id']);loaded['analyses'].append(result)
                self.assertEqual(loaded['analyses'][0],snapshot)
                self.assertEqual(result['parameters'],old['parameters'])
                self.assertEqual(result['values']['p'],old['values']['p'])
                self.assertEqual(result['parent_analysis_id'],old['analysis_id'])
                validate_document(loaded)

    def test_two_sample_analytic_t2_and_direction(self):
        document=self.document()
        r=self.run_record(document,'two',[0,1],equal_var=True)
        self.assertAlmostEqual(r['values']['t'],-math.sqrt(2),places=12)
        self.assertAlmostEqual(r['values']['p'],1-1/math.sqrt(2),places=12)
        self.assertEqual(r['values']['df'],2)
        self.assertEqual(r['missing']['counts'],[2,2])

    def test_welch_fractional_or_truncated_degrees_preserved(self):
        document=new_document(['A','B'],[['0','2'],['2','4'],['','10']])
        for legacy,expected in ((True,2),(False,3721/1433)):
            r=self.run_record(document,'two',[0,1],legacy_df=legacy,alternative='greater',null=-1,confidence=90)
            self.assertAlmostEqual(r['values']['df'],expected,places=12)
            new=rerun_analysis(document,r['analysis_id'])
            self.assertEqual(new['parameters']['legacy_df'],legacy)
            self.assertEqual(new['values']['p'],r['values']['p'])

    def test_summary_immutable_and_independent_from_data_edits(self):
        document=self.document();summary=[dict(n=3,mean=-2.,sd=1.)]
        r=self.run_record(document,'paired',source='summary',summaries=summary,perform_test=False)
        summary[0]['mean']=999
        self.assertEqual(r['parameters']['summaries'][0]['mean'],-2.)
        self.assertEqual(r['source']['column_ids'],[])
        sheet=active_sheet(document);sync_sheet(sheet,['Outro'],[['999']])
        self.assertFalse(is_stale(r,sheet))
        new=rerun_analysis(document,r['analysis_id'])
        self.assertEqual(new['values'],r['values'])
        self.assertNotIn('Valor-p',new['report'])
        self.assertEqual(new['missing']['counts'],[None])

    def test_stacked_order_does_not_reverse_when_rows_reordered(self):
        document=self.document();old=self.run_record(document,'two',[2,3],source='stacked',alternative='less')
        sheet=active_sheet(document)
        sync_sheet(sheet,[c['name'] for c in sheet['columns']],list(reversed(sheet['rows'])))
        new=rerun_analysis(document,old['analysis_id'])
        self.assertEqual(new['parameters']['group_order'],['A','B'])
        self.assertEqual(new['values']['estimate'],old['values']['estimate'])
        self.assertEqual(new['values']['p'],old['values']['p'])
        self.assertIn('ordem dos grupos preservada',new['report'])

    def test_replaced_group_is_refused(self):
        document=self.document();old=self.run_record(document,'two',[2,3],source='stacked')
        sheet=active_sheet(document);rows=deepcopy(sheet['rows']);rows[-1][3]='C'
        sync_sheet(sheet,[c['name'] for c in sheet['columns']],rows)
        with self.assertRaises(ValueError):rerun_analysis(document,old['analysis_id'])
        self.assertEqual(len(document['analyses']),1)

    def test_input_fingerprint_ignores_unrelated_column_and_rename(self):
        document=self.document();r=self.run_record(document,'one',[0]);sheet=active_sheet(document)
        rows=deepcopy(sheet['rows']);rows[0][1]='1000'
        sync_sheet(sheet,['A renomeado','B','Resposta','Grupo'],rows)
        self.assertFalse(is_stale(r,sheet))
        rows[0][0]='1000';sync_sheet(sheet,['A renomeado','B','Resposta','Grupo'],rows)
        self.assertTrue(is_stale(r,sheet))

    def test_legacy_03_record_without_input_fingerprint_reopens(self):
        document=self.document();r=self.run_record(document,'one',[0])
        r['source'].pop('input_fingerprint');r['source'].pop('kind')
        validate_document(document)
        self.assertEqual(rerun_analysis(document,r['analysis_id'])['values']['p'],r['values']['p'])

    def test_invalid_persisted_parameters_rejected(self):
        document=self.document();r=self.run_record(document,'two',[2,3],source='stacked')
        for key,value in [('group_order',['A','A']),('legacy_df','yes'),('summaries',[]),('store_differences',True)]:
            candidate=deepcopy(document);candidate['analyses'][0]['parameters'][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):validate_document(candidate)


class TAnalysisHistoryInterfaceTests(unittest.TestCase):
    def setUp(self):
        from app import MiniTaBom
        from history import WorksheetHistory
        self.app=MiniTaBom();self.app.withdraw();self.addCleanup(self.app.destroy)
        self.app.headers=['A','B'];self.app.rows=[['0','0'],['2','0'],['*','1']]
        self.app.history=WorksheetHistory(self.app.headers,self.app.rows);self.app.refresh()

    def test_paired_storage_rerun_into_original_inactive_sheet_then_undo(self):
        self.assertTrue(self.app.run_ttest('paired',0,1,store=True))
        old=deepcopy(self.app.document['analyses'][0]);first=self.app.document['active_worksheet_id']
        self.assertFalse(is_stale(old,active_sheet(self.app.document)))
        self.app.add_worksheet('Outra');second=self.app.document['active_worksheet_id']
        self.assertTrue(self.app.rerun_saved_analysis(old['analysis_id']))
        self.assertEqual(self.app.document['active_worksheet_id'],second)
        self.assertEqual(old,self.app.document['analyses'][0])
        sheet=next(s for s in self.app.document['worksheets'] if s['id']==first)
        self.assertEqual(len(sheet['columns']),4)
        self.assertNotEqual(old['storage']['column_ids'],self.app.document['analyses'][-1]['storage']['column_ids'])
        self.assertFalse(is_stale(self.app.document['analyses'][-1],sheet))
        self.app.switch_worksheet(first);self.app.undo_data();self.assertEqual(len(self.app.headers),3)
        self.app.redo_data();self.assertEqual(len(self.app.headers),4)
        self.assertEqual(active_sheet(self.app.document)['columns'][-1]['id'],
                         self.app.document['analyses'][-1]['storage']['column_ids'][0])

    def test_analysis_of_generated_column_survives_undo_redo_identity(self):
        self.app.run_ttest('paired',0,1,store=True)
        self.app.run_ttest('one',2)
        result=self.app.document['analyses'][-1]
        key=result['source']['column_ids'][0]
        self.app.undo_data()
        with patch('app.messagebox.showerror'):
            self.assertFalse(self.app.rerun_saved_analysis(result['analysis_id']))
        self.app.redo_data()
        self.assertEqual(active_sheet(self.app.document)['columns'][2]['id'],key)
        self.assertTrue(self.app.rerun_saved_analysis(result['analysis_id']))
        self.assertEqual(self.app.document['analyses'][-1]['values']['p'],result['values']['p'])

    def test_failed_storage_and_failed_rerun_leave_rows_and_results_unchanged(self):
        before=deepcopy(self.app.rows)
        with patch('app.messagebox.showerror'):
            self.assertFalse(self.app.run_ttest('one',0,store=True))
        self.assertEqual(self.app.rows,before);self.assertEqual(self.app.document['analyses'],[])
        self.app.run_ttest('paired',0,1,store=True)
        old=self.app.document['analyses'][0]
        self.app.rows=[['1','1','0']]*3;self.app.data_changed()
        snapshot=deepcopy(self.app.document);output=self.app.output.get('1.0','end')
        with patch('app.messagebox.showerror'):
            self.assertFalse(self.app.rerun_saved_analysis(old['analysis_id']))
        self.assertEqual(self.app.document,snapshot);self.assertEqual(self.app.output.get('1.0','end'),output)

    def test_summary_history_roundtrip_rerun_on_empty_sheet(self):
        self.app.new_project()
        summary=[dict(n=3,mean=-2.,sd=1.)]
        self.assertTrue(self.app.run_ttest('paired',source='summary',summaries=summary))
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'summary.statlab';self.app.project_path=str(path);self.app.save_project()
            with patch('app.filedialog.askopenfilename',return_value=str(path)):self.app.open_project()
            r=self.app.document['analyses'][0]
            self.assertTrue(self.app.rerun_saved_analysis(r['analysis_id']))
            self.assertEqual(self.app.rows,[])
            dialog=self.app.analysis_history_dialog()
            self.assertEqual(dialog.tree.item(r['analysis_id'],'values')[-1],'Resumo informado')
            dialog.destroy()
