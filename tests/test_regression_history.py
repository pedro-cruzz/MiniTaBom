from copy import deepcopy
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from regression_service import execute_regression, archived_model, model_for_prediction
from analysis_service import rerun_analysis
from workspace_model import new_document, active_sheet, sync_sheet, validate_document
from project import save_document, load_document
from prediction import predict_linear


class RegressionHistoryTests(unittest.TestCase):
    def sample(self):
        return new_document(['X','Y','Extra'],[['0','1','a'],['1','2','b'],['2','4','c'],['3','4','d'],['*','9','e']])

    def fit(self,document,**options):
        sheet=active_sheet(document)
        result=execute_regression(sheet,[sheet['columns'][1]['id'],sheet['columns'][0]['id']],show_graph=False,**options)
        document['analyses'].append(result)
        return result

    def test_roundtrip_predicts_without_refitting_analytic_fit_and_se(self):
        document=self.sample();result=self.fit(document,confidence=90,observations=True)
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'model.statlab';save_document(path,document);loaded=load_document(path)
        self.assertEqual(loaded,document)
        with patch('regression_service.linear_regression',side_effect=AssertionError('must not refit')):
            model=model_for_prediction(loaded['analyses'][0],active_sheet(loaded))
            predicted=predict_linear(model,[[4.]])
        self.assertAlmostEqual(model['terms'][0]['coefficient'],1.1,places=12)
        self.assertAlmostEqual(model['terms'][1]['coefficient'],1.1,places=12)
        self.assertAlmostEqual(predicted['cases'][0]['fit'],5.5,places=12)
        self.assertAlmostEqual(predicted['cases'][0]['se_fit'],math.sqrt(.525),places=12)
        self.assertEqual(predicted['confidence'],90)
        self.assertEqual(result['missing']['count'],1)

    def test_multiple_perfect_model_persists_and_predicts(self):
        rows=[[str(x),str(z),str(1+2*x-3*z)] for x,z in [(1,2),(2,0),(3,1),(4,3),(5,5),(6,1)]]
        document=new_document(['X','Z','Y'],rows);sheet=active_sheet(document)
        result=execute_regression(sheet,[sheet['columns'][i]['id'] for i in (2,0,1)],show_graph=False)
        document['analyses'].append(result);validate_document(document)
        model=archived_model(result);prediction=predict_linear(model,[[7.,2.]])
        self.assertTrue(model['perfect']);self.assertAlmostEqual(prediction['cases'][0]['fit'],9.,places=12)
        self.assertEqual(prediction['cases'][0]['ci'][0],prediction['cases'][0]['ci'][1])

    def test_rerun_preserves_previous_and_resolves_ids_after_reorder(self):
        document=self.sample();old=self.fit(document);snapshot=deepcopy(old);sheet=active_sheet(document)
        sync_sheet(sheet,['Y','X','Extra'],[[r[1],r[0],r[2]] for r in sheet['rows']])
        sync_sheet(sheet,['Y novo','X','Extra'],sheet['rows'])
        result=rerun_analysis(document,old['analysis_id']);document['analyses'].append(result)
        self.assertEqual(document['analyses'][0],snapshot)
        self.assertEqual(result['parent_analysis_id'],old['analysis_id'])
        self.assertEqual(result['values']['response'],'Y novo')
        self.assertEqual(result['values']['terms'][1]['coefficient'],old['values']['terms'][1]['coefficient'])
        validate_document(document)

    def test_unrelated_edits_do_not_invalidate_but_input_edits_do(self):
        document=self.sample();result=self.fit(document);sheet=active_sheet(document)
        rows=deepcopy(sheet['rows']);rows[0][2]='new';sync_sheet(sheet,['X renomeado','Y','Extra'],rows)
        self.assertEqual(model_for_prediction(result,sheet)['predictors'],['X renomeado'])
        rows[0][1]='99';sync_sheet(sheet,['X renomeado','Y','Extra'],rows)
        with self.assertRaises(ValueError):model_for_prediction(result,sheet)
        self.assertEqual(archived_model(result)['observed'][0],1.)

    def test_corrupt_model_shapes_numbers_flags_and_selected_reference_refused(self):
        document=self.sample();self.fit(document)
        changes=[lambda d:d['analyses'][0]['values']['prediction_state'].update(x_scale=[0.]),
                 lambda d:d['analyses'][0]['values']['prediction_state'].update(inverse_factor=[[1.]]),
                 lambda d:d['analyses'][0]['values'].update(df_error=0),
                 lambda d:d['analyses'][0]['values'].update(leverage=[0.]*3),
                 lambda d:d['analyses'][0]['values']['terms'][0].update(coefficient=math.nan),
                 lambda d:d['analyses'][0]['parameters'].update(store='yes'),
                 lambda d:d['analyses'][0].update(scenes=[]),
                 lambda d:d['metadata'].update(active_regression_by_sheet=[]),
                 lambda d:d['metadata'].update(active_regression_by_sheet={active_sheet(d)['id']:'missing'})]
        for change in changes:
            candidate=deepcopy(document);change(candidate)
            with self.subTest(change=change),self.assertRaises(ValueError):validate_document(candidate)


class RegressionHistoryInterfaceTests(unittest.TestCase):
    def setUp(self):
        from app import MiniTaBom
        self.app=MiniTaBom();self.app.withdraw();self.addCleanup(self.app.destroy)
        self.app.headers=['X','Y','Extra'];self.app.rows=[['0','1','a'],['1','2','b'],['2','4','c'],['3','4','d']]
        self.app.refresh()

    def test_save_reopen_restores_model_and_prediction_without_fit(self):
        self.assertTrue(self.app.run_regression(1,[0],show_graph=False))
        key=self.app.last_regression_id
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'restore.statlab';self.app.project_path=str(path);self.app.save_project()
            with patch('app.filedialog.askopenfilename',return_value=str(path)),patch('regression_service.linear_regression',side_effect=AssertionError('must not fit')):
                self.app.open_project()
            self.assertEqual(self.app.last_regression_id,key)
            self.assertTrue(self.app.run_prediction(text='4'))
            self.assertIn('Previsão = 5.5',self.app.output.get('1.0','end'))

    def test_edit_invalidation_undo_restoration_and_labels(self):
        from history import WorksheetHistory
        self.app.history=WorksheetHistory(self.app.headers,self.app.rows);self.app.refresh()
        self.app.run_regression(1,[0],show_graph=False)
        key=self.app.last_regression_id
        self.app.rows[0][2]='other';self.app.data_changed();self.assertEqual(self.app.last_regression_id,key)
        self.app.rows[0][1]='99';self.app.data_changed();self.assertIsNone(self.app.last_regression)
        self.app.undo_data();self.assertEqual(self.app.last_regression_id,key)
        with patch('app.simpledialog.askstring',return_value='X novo'):self.app.rename_column(0)
        self.assertEqual(self.app.last_regression['predictors'],['X novo'])

    def test_selected_model_per_sheet_reopens_and_switches_without_refitting(self):
        self.app.run_regression(1,[0],show_graph=False,confidence=90)
        first=self.app.document['active_worksheet_id'];old=self.app.last_regression_id
        self.app.run_regression(1,[0],show_graph=False,confidence=99)
        self.assertTrue(self.app.use_saved_regression(old));self.assertEqual(self.app.last_regression['confidence'],90)
        self.app.add_worksheet('Outra');self.assertIsNone(self.app.last_regression)
        self.app.headers=['A','B'];self.app.rows=[['0','2'],['1','4'],['2','5'],['3','8']];self.app.refresh()
        self.app.run_regression(1,[0],show_graph=False);second=self.app.last_regression_id
        self.app.switch_worksheet(first);self.assertEqual(self.app.last_regression_id,old)
        self.assertNotEqual(second,old)
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'selected.statlab';self.app.project_path=str(path);self.app.save_project()
            with patch('app.filedialog.askopenfilename',return_value=str(path)):self.app.open_project()
            self.assertEqual(self.app.last_regression_id,old)

    def test_stale_model_can_show_historical_graph_but_cannot_activate(self):
        self.app.run_regression(1,[0],show_graph=False);result=self.app.document['analyses'][-1]
        self.app.rows[0][1]='99';self.app.data_changed()
        with patch('app.messagebox.showerror'):
            self.assertFalse(self.app.use_saved_regression(result['analysis_id']))
        graph=self.app.show_saved_regression_graph(result['analysis_id']);graph.withdraw();graph.draw()
        self.assertEqual(graph.result['observed'][0],1.)
        self.assertGreater(len(graph.canvas.find_all()),10);graph.destroy()

    def test_rerun_storage_keeps_old_and_new_columns_and_history(self):
        self.app.run_regression(1,[0],show_graph=False,store=True)
        old=deepcopy(self.app.document['analyses'][-1]);first=self.app.document['active_worksheet_id']
        self.app.add_worksheet('Outra');second=self.app.document['active_worksheet_id']
        self.assertTrue(self.app.rerun_saved_analysis(old['analysis_id']))
        self.assertEqual(self.app.document['active_worksheet_id'],second)
        self.assertEqual(self.app.document['analyses'][0],old)
        self.app.switch_worksheet(first)
        self.assertEqual(len(self.app.headers),13)
        self.app.undo_data();self.assertEqual(len(self.app.headers),8)
        self.app.redo_data();self.assertEqual(len(self.app.headers),13)
        self.assertIsNotNone(self.app.last_regression)

    def test_invalid_model_open_keeps_current_document_and_cache(self):
        self.app.run_regression(1,[0],show_graph=False)
        before=deepcopy(self.app.document);key=self.app.last_regression_id
        invalid=deepcopy(before);invalid['analyses'][0]['values']['prediction_state']['x_scale']=[0.]
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'invalid.statlab'
            import json
            path.write_text(json.dumps(invalid),encoding='utf-8')
            with patch('app.filedialog.askopenfilename',return_value=str(path)),patch('app.messagebox.showerror'):
                self.app.open_project()
        self.assertEqual(self.app.document,before);self.assertEqual(self.app.last_regression_id,key)
