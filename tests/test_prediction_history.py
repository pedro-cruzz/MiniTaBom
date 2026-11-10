from copy import deepcopy
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from workspace_model import new_document,active_sheet,sync_sheet,validate_document,is_stale,unpack_numbers
from regression_service import execute_regression
from prediction_service import execute_prediction
from analysis_service import rerun_analysis
from project import save_document,load_document


class PredictionHistoryTests(unittest.TestCase):
    def sample(self):
        document=new_document(['X','Y','Novo X'],[['0','1','4'],['1','2','*'],['2','4','5'],['3','4','']])
        sheet=active_sheet(document)
        model=execute_regression(sheet,[sheet['columns'][i]['id'] for i in (1,0)],show_graph=False)
        document['analyses'].append(model)
        return document,model

    def predict(self,document,model,**options):
        result=execute_prediction(document,model['analysis_id'],active_sheet(document)['id'],**options)
        document['analyses'].append(result)
        return result

    def test_roundtrip_analytic_intervals_and_recalculation_without_refit(self):
        document,model=self.sample();r=self.predict(document,model,cases=[[4.]],confidence=95)
        case=r['values']['cases'][0]
        critical=math.sqrt(2*.95**2/(1-.95**2))  # exact t2 quantile
        self.assertAlmostEqual(case['fit'],5.5,places=12)
        self.assertAlmostEqual(case['se_fit'],math.sqrt(.525),places=12)
        self.assertAlmostEqual(case['ci'][1]-case['fit'],critical*math.sqrt(.525),places=10)
        self.assertAlmostEqual(case['pi'][1]-case['fit'],critical*math.sqrt(.875),places=10)
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'prediction.statlab';save_document(path,document);loaded=load_document(path)
        with patch('regression_service.linear_regression',side_effect=AssertionError('must not refit')):
            new=rerun_analysis(loaded,r['analysis_id'])
        self.assertEqual(new['values'],r['values']);self.assertEqual(new['parent_analysis_id'],r['analysis_id'])

    def test_one_sided_infinite_bounds_are_explicit_json_tags(self):
        for alternative,bound in [('lower',1),('upper',0)]:
            document,model=self.sample();r=self.predict(document,model,cases=[[4]],alternative=alternative)
            self.assertIn('$statlab_number',r['values']['cases'][0]['ci'][bound])
            with tempfile.TemporaryDirectory() as directory:
                path=Path(directory)/'one-sided.statlab';save_document(path,document);loaded=load_document(path)
            self.assertTrue(math.isinf(unpack_numbers(loaded['analyses'][-1]['values'])['cases'][0]['pi'][bound]))

    def test_pinned_model_and_cases_ignore_later_training_changes_and_models(self):
        document,model=self.sample();cases=[[4.]];r=self.predict(document,model,cases=cases)
        cases[0][0]=999;old=deepcopy(r)
        sheet=active_sheet(document);rows=deepcopy(sheet['rows'])
        for row in rows:row[1]=str(float(row[1])+100)
        sync_sheet(sheet,['X','Y','Novo X'],rows)
        newer=execute_regression(sheet,[sheet['columns'][i]['id'] for i in (1,0)],show_graph=False);document['analyses'].append(newer)
        self.assertFalse(is_stale(r,sheet))
        new=rerun_analysis(document,r['analysis_id']);document['analyses'].append(new)
        self.assertEqual(r,old);self.assertEqual(new['values']['cases'][0]['fit'],old['values']['cases'][0]['fit'])
        self.assertEqual(new['parameters']['model_analysis_id'],model['analysis_id']);validate_document(document)

    def test_column_mapping_missing_policy_and_current_values(self):
        document,model=self.sample();sheet=active_sheet(document);key=sheet['columns'][2]['id']
        r=self.predict(document,model,input_kind='columns',input_column_ids=[key])
        self.assertEqual(r['values']['omitted'],[2,4]);self.assertEqual([c['case'] for c in r['values']['cases']],[1,3])
        rows=deepcopy(sheet['rows']);rows[0][2]='6';sync_sheet(sheet,['X','Y','Outro nome'],rows)
        self.assertTrue(is_stale(r,sheet));new=rerun_analysis(document,r['analysis_id'])
        self.assertEqual(new['values']['cases'][0]['values'],[6.])
        self.assertAlmostEqual(new['values']['cases'][0]['fit'],7.7,places=12)
        self.assertEqual(new['parameters']['model_analysis_id'],model['analysis_id'])
        with self.assertRaises(ValueError):
            self.predict(document,model,input_kind='columns',input_column_ids=[key],omit_missing=False)

    def test_columns_on_other_sheet_and_deleted_mapping(self):
        from workspace_model import new_sheet
        document,model=self.sample();sheet=new_sheet('Novos casos',['Entrada'],[['4'],['6']]);document['worksheets'].append(sheet)
        r=execute_prediction(document,model['analysis_id'],sheet['id'],input_kind='columns',input_column_ids=[sheet['columns'][0]['id']])
        document['analyses'].append(r);validate_document(document)
        self.assertAlmostEqual(r['values']['cases'][1]['fit'],7.7,places=12)
        sync_sheet(sheet,['Substituta'],[['8']])  # rename preserves identity
        self.assertTrue(rerun_analysis(document,r['analysis_id']))
        sheet['columns'][0]['id']='replacement';sync_sheet(sheet,['Substituta'],sheet['rows'])
        with self.assertRaises(ValueError):rerun_analysis(document,r['analysis_id'])

    def test_invalid_model_reference_parameters_and_intervals_refused(self):
        document,model=self.sample();self.predict(document,model,cases=[[4.]])
        for change in [lambda d:d['analyses'][-1]['parameters'].update(model_analysis_id='missing'),
                       lambda d:d['analyses'][-1]['parameters'].update(cases=[[math.nan]]),
                       lambda d:d['analyses'][-1]['parameters'].update(case_numbers=[0]),
                       lambda d:d['analyses'][-1]['parameters'].update(input_column_ids=['unexpected']),
                       lambda d:d['analyses'][-1]['values']['cases'][0].update(ci=[10,20]),
                       lambda d:d['analyses'][-1]['values']['cases'][0].update(high_leverage='yes')]:
            invalid=deepcopy(document);change(invalid)
            with self.subTest(change=change),self.assertRaises(ValueError):validate_document(invalid)


class PredictionHistoryInterfaceTests(unittest.TestCase):
    def setUp(self):
        from app import MiniTaBom
        self.app=MiniTaBom();self.app.withdraw();self.addCleanup(self.app.destroy)
        self.app.headers=['X','Y','Novo X'];self.app.rows=[['0','1','4'],['1','2','*'],['2','4','5'],['3','4','']]
        self.app.refresh();self.app.run_regression(1,[0],show_graph=False)

    def test_save_reopen_recalculate_and_export_original(self):
        self.assertTrue(self.app.run_prediction(text='\n4\n5',alternative='lower',confidence=90))
        old=deepcopy(self.app.document['analyses'][-1])
        self.assertEqual(old['parameters']['case_numbers'],[2,3])
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'cases.statlab';self.app.project_path=str(path);self.app.save_project()
            with patch('app.filedialog.askopenfilename',return_value=str(path)):self.app.open_project()
            self.assertTrue(self.app.rerun_saved_analysis(old['analysis_id']))
            self.assertEqual(self.app.document['analyses'][-1]['values'],old['values'])
            dialog=self.app.analysis_history_dialog();dialog.tree.selection_set(old['analysis_id']);dialog.show()
            self.assertEqual(dialog.rerun_button.cget('text'),'Recalcular casos salvos')
            self.assertEqual(dialog.tree.item(old['analysis_id'],'values')[-1],'Modelo/casos fixos')
            export=Path(directory)/'prediction.json'
            with patch('analysis_history_dialog.filedialog.asksaveasfilename',return_value=str(export)):dialog.export()
            import json
            self.assertEqual(json.loads(export.read_text(encoding='utf-8')),old);dialog.destroy()

    def test_invalid_new_forecast_is_atomic_and_column_recalculation_works(self):
        self.app.sync_document()
        before=deepcopy(self.app.document);text=self.app.output.get('1.0','end')
        with patch('app.messagebox.showerror'):
            self.assertFalse(self.app.run_prediction(columns=[2],omit_missing=False))
        self.assertEqual(self.app.document,before);self.assertEqual(self.app.output.get('1.0','end'),text)
        self.app.run_prediction(columns=[2]);old=self.app.document['analyses'][-1]
        self.app.rows[0][2]='6';self.app.data_changed()
        self.assertTrue(self.app.rerun_saved_analysis(old['analysis_id']))
        self.assertEqual(self.app.document['analyses'][-1]['values']['cases'][0]['values'],[6.])

    def test_recalculate_existing_forecast_after_model_training_changes(self):
        self.app.run_prediction(text='4');old=self.app.document['analyses'][-1]
        self.app.rows[0][1]='99';self.app.data_changed();self.assertIsNone(self.app.last_regression)
        with patch('app.messagebox.showerror'):self.assertFalse(self.app.run_prediction(text='4'))
        self.assertTrue(self.app.rerun_saved_analysis(old['analysis_id']))
        self.assertEqual(self.app.document['analyses'][-1]['values']['cases'][0]['fit'],old['values']['cases'][0]['fit'])
