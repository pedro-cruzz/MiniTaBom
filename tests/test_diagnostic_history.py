from copy import deepcopy
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from diagnostic_service import execute_normality,execute_study
from workspace_model import new_document,active_sheet,sync_sheet,validate_document,is_stale
from analysis_service import rerun_analysis
from project import save_document,load_document


class DiagnosticHistoryTests(unittest.TestCase):
    def test_size_limit_does_not_replace_existing_project(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'safe.statlab';document=new_document(['A'],[['1']]);save_document(path,document)
            before=path.read_bytes()
            with patch('project.MAX_PROJECT_BYTES',100),self.assertRaises(ValueError):save_document(path,document)
            self.assertEqual(path.read_bytes(),before);self.assertEqual(list(Path(directory).iterdir()),[path])

    def test_all_five_normality_methods_roundtrip_and_rerun(self):
        for method in ('ad','rj','ks','shapiro','dagostino'):
            document=new_document(['A'],[[str(x)] for x in [1,2,3,4,5,6,7,9,11,14,15,18]]+[['*'],['']])
            sheet=active_sheet(document)
            with self.subTest(method=method):
                r=execute_normality(sheet,[sheet['columns'][0]['id']],method=method);document['analyses'].append(r)
                self.assertEqual(r['missing']['count'],2)
                with tempfile.TemporaryDirectory() as directory:
                    path=Path(directory)/'normality.statlab';save_document(path,document);loaded=load_document(path)
                new=rerun_analysis(loaded,r['analysis_id']);loaded['analyses'].append(new)
                self.assertEqual(new['values'],r['values']);self.assertEqual(new['parameters'],r['parameters'])
                validate_document(loaded)

    def test_bounded_pvalue_is_not_changed_to_a_point_probability(self):
        document=new_document(['A'],[[str(i)] for i in range(1,9)]);sheet=active_sheet(document)
        r=execute_normality(sheet,[sheet['columns'][0]['id']],method='rj');document['analyses'].append(r)
        self.assertIsNone(r['values']['p']);self.assertEqual(r['values']['p_lower'],.1)
        self.assertIn('> 0.1',r['report'])
        self.assertEqual(rerun_analysis(document,r['analysis_id'])['values']['p_lower'],.1)

    def test_mannwhitney_exact_tail_and_wilcoxon_exact_signs(self):
        document=new_document(['A','B'],[['1','4'],['2','5'],['3','6']]);sheet=active_sheet(document)
        r=execute_study(sheet,[c['id'] for c in sheet['columns']],'mannwhitney',method='exact')
        self.assertAlmostEqual(r['values']['p'],.1,places=12);self.assertEqual(r['values']['statistic'],0.)
        self.assertEqual(r['parameters']['method'],'exact');self.assertEqual(r['values']['method'],'exact')
        sync_sheet(sheet,['A','B'],[['1','4'],['2','6'],['3','8']])
        r=execute_study(sheet,[c['id'] for c in sheet['columns']],'wilcoxon',method='exact')
        self.assertEqual(r['values']['p'],.25);self.assertEqual(r['values']['zeros'],0)

    def test_zero_rules_ties_and_effective_automatic_method_persist(self):
        for zero in ('wilcox','pratt','zsplit'):
            document=new_document(['A','B'],[['1','1'],['3','2'],['1','3'],['4','2']]);sheet=active_sheet(document)
            r=execute_study(sheet,[c['id'] for c in sheet['columns']],'wilcoxon',zero_method=zero,correction=False)
            document['analyses'].append(r)
            self.assertEqual(r['parameters']['method'],'auto');self.assertEqual(r['values']['method'],'asymptotic')
            self.assertEqual(r['values']['zeros'],1);self.assertTrue(r['values']['ties'])
            self.assertEqual(rerun_analysis(document,r['analysis_id'])['values'],r['values'])

    def test_all_zero_differences_keep_the_explicit_convention(self):
        document=new_document(['A','B'],[['1','1'],['2','2'],['3','3']]);sheet=active_sheet(document)
        r=execute_study(sheet,[c['id'] for c in sheet['columns']],'wilcoxon');document['analyses'].append(r)
        self.assertEqual(r['values']['p'],1.);self.assertEqual(r['values']['zeros'],3)
        self.assertIn('todas as diferenças são zero',r['values']['method']);validate_document(document)

    def test_kruskal_analytic_chisquare_tail(self):
        document=new_document(['A','B','C'],[['1','4','7'],['2','5','8'],['3','6','9']]);sheet=active_sheet(document)
        r=execute_study(sheet,[c['id'] for c in sheet['columns']],'kruskal');document['analyses'].append(r)
        self.assertAlmostEqual(r['values']['statistic'],7.2,places=12)
        self.assertAlmostEqual(r['values']['p'],math.exp(-3.6),places=12);self.assertEqual(r['values']['df'],2)
        self.assertEqual(rerun_analysis(document,r['analysis_id'])['values'],r['values'])

    def test_variance_methods_and_group_degrees_are_preserved(self):
        document=new_document(['A','B','C'],[[str(x),str(2*x-1),str(3*x-1)] for x in range(1,6)]);sheet=active_sheet(document)
        for center in ('median','mean','bartlett'):
            r=execute_study(sheet,[c['id'] for c in sheet['columns']],'variances',center=center);document['analyses'].append(r)
            self.assertEqual(r['values']['df'],2 if center=='bartlett' else [2,12])
            self.assertEqual(rerun_analysis(document,r['analysis_id'])['parameters']['center'],center)
        validate_document(document)

    def test_stacked_order_and_one_sided_comparison_survive_row_reorder(self):
        document=new_document(['Valor','Grupo'],[['1','A'],['2','A'],['3','A'],['4','B'],['5','B'],['6','B']]);sheet=active_sheet(document)
        r=execute_study(sheet,[c['id'] for c in sheet['columns']],'mannwhitney',input_kind='stacked',alternative='less',method='exact')
        document['analyses'].append(r);old=deepcopy(r)
        sync_sheet(sheet,['Valor novo','Grupo'],list(reversed(sheet['rows'])))
        new=rerun_analysis(document,r['analysis_id'])
        self.assertEqual(new['parameters']['group_order'],['A','B']);self.assertEqual(new['values']['p'],.05)
        self.assertEqual(r,old)
        rows=deepcopy(sheet['rows']);rows[0][1]='C';sync_sheet(sheet,['Valor novo','Grupo'],rows)
        with self.assertRaises(ValueError):rerun_analysis(document,r['analysis_id'])

    def test_invalid_pvalue_bounds_snapshots_and_options_are_rejected(self):
        document=new_document(['A'],[[str(i)] for i in range(1,9)]);sheet=active_sheet(document)
        r=execute_normality(sheet,[sheet['columns'][0]['id']],method='rj');document['analyses'].append(r)
        for change in [lambda d:d['analyses'][0]['values'].update(p_upper=.01),
                       lambda d:d['analyses'][0]['scenes'][0].update(sample=[1.]),
                       lambda d:d['analyses'][0]['parameters'].update(show_graph='yes')]:
            invalid=deepcopy(document);change(invalid)
            with self.assertRaises(ValueError):validate_document(invalid)


class DiagnosticHistoryInterfaceTests(unittest.TestCase):
    def setUp(self):
        from app import MiniTaBom
        self.app=MiniTaBom();self.app.withdraw();self.addCleanup(self.app.destroy)
        self.app.headers=['A','B'];self.app.rows=[[str(x),str(2*x+1)] for x in [1,2,3,4,5,7,9,11]];self.app.refresh()

    def test_reopen_historical_probability_graph_and_reexecute_current_data(self):
        self.app.run_normality(0,method='rj');old=deepcopy(self.app.document['analyses'][-1])
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'diagnostic.statlab';self.app.project_path=str(path);self.app.save_project()
            with patch('app.filedialog.askopenfilename',return_value=str(path)):self.app.open_project()
            self.app.rows[0][0]='20';self.app.data_changed()
            graph=self.app.show_saved_normality_graph(old['analysis_id']);graph.withdraw();graph.draw()
            self.assertEqual(graph.values,sorted(old['scenes'][0]['sample']));graph.destroy()
            self.assertTrue(self.app.rerun_saved_analysis(old['analysis_id']))
            self.assertEqual(self.app.document['analyses'][0],old)
            self.assertNotEqual(self.app.document['analyses'][-1]['values']['mean'],old['values']['mean'])
            dialog=self.app.analysis_history_dialog();dialog.tree.selection_set(old['analysis_id']);dialog.show()
            self.assertEqual(str(dialog.graph.cget('state')),'normal');dialog.destroy()

    def test_rerun_with_graph_releases_modal_history_grab(self):
        self.app.run_normality(0,method='rj',show_graph=True)
        dialog=self.app.analysis_history_dialog();dialog.rerun()
        self.assertIsNone(self.app.grab_current());dialog.destroy()

    def test_failed_exact_after_new_ties_is_atomic(self):
        self.app.run_study('mannwhitney',columns=[0,1],method='auto')
        self.app.rows=[['1','4'],['2','5'],['3','6']];self.app.data_changed();self.app.refresh()
        self.assertTrue(self.app.run_study('mannwhitney',columns=[0,1],method='exact'))
        old=self.app.document['analyses'][-1]
        self.app.rows[0][1]='1';self.app.data_changed();self.app.sync_document()
        before=deepcopy(self.app.document);output=self.app.output.get('1.0','end')
        with patch('app.messagebox.showerror'):self.assertFalse(self.app.rerun_saved_analysis(old['analysis_id']))
        self.assertEqual(self.app.document,before);self.assertEqual(self.app.output.get('1.0','end'),output)

    def test_independent_history_for_all_modes_and_removed_column(self):
        for mode in ('mannwhitney','wilcoxon','kruskal','variances'):
            self.assertTrue(self.app.run_study(mode,columns=[0,1]))
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'all.statlab';self.app.project_path=str(path);self.app.save_project()
            with patch('app.filedialog.askopenfilename',return_value=str(path)):self.app.open_project()
            for record in list(self.app.document['analyses']):self.assertTrue(self.app.rerun_saved_analysis(record['analysis_id']))
            old=self.app.document['analyses'][0]
            self.app.headers=['B'];self.app.rows=[[r[1]] for r in self.app.rows];self.app.refresh()
            with patch('app.messagebox.showerror'):self.assertFalse(self.app.rerun_saved_analysis(old['analysis_id']))
