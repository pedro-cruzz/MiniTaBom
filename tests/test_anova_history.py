from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from anova_service import execute_anova
from workspace_model import new_document,active_sheet,sync_sheet,validate_document
from analysis_service import rerun_analysis
from project import save_document,load_document


class AnovaHistoryTests(unittest.TestCase):
    def sample(self):return new_document(['A','B','C'],[['1','4','7'],['2','5','8'],['3','6','9']])

    def fit(self,document,**options):
        sheet=active_sheet(document)
        r=execute_anova(sheet,[c['id'] for c in sheet['columns']],**options);document['analyses'].append(r)
        return r

    def test_analytic_classical_roundtrip_and_rerun(self):
        document=self.sample();r=self.fit(document,confidence=90)
        self.assertEqual(r['values']['f'],27.)
        self.assertAlmostEqual(r['values']['p'],.001,places=13)
        self.assertEqual((r['values']['ss_between'],r['values']['ss_within']),(54.,6.))
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'anova.statlab';save_document(path,document);loaded=load_document(path)
        self.assertEqual(document,loaded)
        new=rerun_analysis(loaded,r['analysis_id']);loaded['analyses'].append(new)
        self.assertEqual(new['values'],r['values']);self.assertEqual(new['parameters'],r['parameters'])
        self.assertEqual(new['parent_analysis_id'],r['analysis_id']);validate_document(loaded)

    def test_all_comparisons_persist_with_adjustment_convention(self):
        for equal_var,method,label in [(True,'tukey','Tukey-Kramer'),(True,'lsd','Fisher LSD'),(False,'tukey','Games-Howell')]:
            document=self.sample();r=self.fit(document,equal_var=equal_var,comparisons=True,comparison_method=method)
            with self.subTest(equal_var=equal_var,method=method):
                self.assertTrue(r['values']['comparison_method'].startswith(label))
                self.assertEqual(len(r['values']['comparisons']),3)
                self.assertEqual(rerun_analysis(document,r['analysis_id'])['values']['comparisons'],r['values']['comparisons'])
                validate_document(document)

    def test_stacked_order_is_preserved_and_new_group_refused(self):
        rows=[[str(v),g] for g,values in [('B',[4,5,6]),('A',[1,2,3]),('C',[7,8,9])] for v in values]
        document=new_document(['Resposta','Fator'],rows);sheet=active_sheet(document)
        r=execute_anova(sheet,[c['id'] for c in sheet['columns']],input_kind='stacked',comparisons=True,comparison_method='lsd')
        document['analyses'].append(r);old=deepcopy(r)
        sync_sheet(sheet,['Resposta','Fator'],list(reversed(rows)))
        new=rerun_analysis(document,r['analysis_id'])
        self.assertEqual(new['parameters']['group_order'],['B','A','C'])
        self.assertEqual(new['values']['comparisons'][0]['difference'],3.)
        self.assertEqual(r,old)
        changed=deepcopy(sheet['rows']);changed[0][1]='D';sync_sheet(sheet,['Resposta','Fator'],changed)
        with self.assertRaises(ValueError):rerun_analysis(document,r['analysis_id'])

    def test_missing_counts_and_snapshot_are_independent_of_new_data(self):
        document=new_document(['A','B'],[['1','3'],['2','4'],['*','5'],['','']]);r=self.fit(document)
        self.assertEqual(r['missing']['count'],3)
        self.assertEqual([g['missing'] for g in r['scenes'][0]['groups']],[2,1])
        sheet=active_sheet(document);sync_sheet(sheet,['A','B'],[['99','4'],['100','5']])
        self.assertEqual(r['scenes'][0]['groups'][0]['values'],[1.,2.])
        self.assertNotEqual(rerun_analysis(document,r['analysis_id'])['values']['overall'],r['values']['overall'])

    def test_invalid_snapshots_options_counts_and_comparisons_refused(self):
        document=self.sample();self.fit(document,comparisons=True)
        changes=[lambda d:d['analyses'][0]['parameters'].update(equal_var='yes'),
                 lambda d:d['analyses'][0]['scenes'][0]['groups'][0].update(values=[]),
                 lambda d:d['analyses'][0]['values'].update(n=99),
                 lambda d:d['analyses'][0]['values'].update(comparisons=[]),
                 lambda d:d['analyses'][0]['values']['comparisons'][0].update(p=-1)]
        for change in changes:
            invalid=deepcopy(document);change(invalid)
            with self.subTest(change=change),self.assertRaises(ValueError):validate_document(invalid)


class AnovaHistoryInterfaceTests(unittest.TestCase):
    def setUp(self):
        from app import MiniTaBom
        self.app=MiniTaBom();self.app.withdraw();self.addCleanup(self.app.destroy)
        self.app.headers=['A','B','C'];self.app.rows=[['1','4','7'],['2','5','8'],['3','6','9']];self.app.refresh()

    def test_reopen_view_historical_graph_and_rerun_preserves_old(self):
        self.assertTrue(self.app.run_anova(columns=[0,1,2],comparisons=True,comparison_method='lsd'))
        old=deepcopy(self.app.document['analyses'][-1])
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'anova.statlab';self.app.project_path=str(path);self.app.save_project()
            with patch('app.filedialog.askopenfilename',return_value=str(path)):self.app.open_project()
            self.app.rows[0][0]='20';self.app.data_changed()
            graph=self.app.show_saved_anova_graph(old['analysis_id']);graph.withdraw();graph.draw()
            self.assertEqual(graph.groups[0]['values'],[1.,2.,3.]);graph.destroy()
            self.assertTrue(self.app.rerun_saved_analysis(old['analysis_id']))
            self.assertEqual(self.app.document['analyses'][0],old)
            dialog=self.app.analysis_history_dialog();dialog.tree.selection_set(old['analysis_id']);dialog.show()
            self.assertEqual(str(dialog.graph.cget('state')),'normal')
            self.assertEqual(str(dialog.use_model.cget('state')),'disabled');dialog.destroy()

    def test_invalid_anova_keeps_rows_history_and_session(self):
        self.app.sync_document();before=deepcopy(self.app.document);text=self.app.output.get('1.0','end')
        with patch('app.messagebox.showerror'):
            self.assertFalse(self.app.run_anova(columns=[0,1],equal_var=False,comparisons=True,comparison_method='lsd'))
        self.assertEqual(self.app.document,before);self.assertEqual(self.app.output.get('1.0','end'),text)
