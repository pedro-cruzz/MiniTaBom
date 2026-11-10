from copy import deepcopy
import json
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from two_poisson import two_poisson
from two_poisson_service import execute_two_poisson
from workspace_model import new_document,active_sheet,sync_sheet,validate_document,unpack_numbers,is_stale
from project import save_document,load_document
from analysis_service import rerun_analysis


class TwoPoissonTests(unittest.TestCase):
    def test_exact_inclusive_binomial_tails_by_enumeration(self):
        q=.25
        for first,second in [(0,0),(0,3),(1,4),(2,1),(5,0)]:
            n=first+second
            mass=[math.comb(n,k)*q**k*(1-q)**(n-k) for k in range(n+1)]
            low=sum(mass[:first+1]);high=sum(mass[first:])
            for alternative,expected in [('less',low),('greater',high),('two-sided',min(1,2*min(low,high)))]:
                with self.subTest(first=first,second=second,alternative=alternative):
                    r=two_poisson(first,1,second,1,length2=3,alternative=alternative)
                    self.assertAlmostEqual(r['exact_p'],expected,places=12)

    def test_normal_statistic_and_pooled_test_leave_ci_unpooled(self):
        r=two_poisson(4,1,1,1)
        self.assertAlmostEqual(r['statistic'],3/math.sqrt(5),places=12)
        self.assertAlmostEqual(r['p'],math.erfc(3/math.sqrt(10)),places=12)
        a=two_poisson(4,1,1,1,length2=3);b=two_poisson(4,1,1,1,length2=3,pooled=True)
        self.assertAlmostEqual(a['statistic'],11/math.sqrt(37),places=12)
        self.assertAlmostEqual(b['statistic'],11/math.sqrt(15),places=12)
        self.assertEqual((a['low'],a['high']),(b['low'],b['high']))
        self.assertEqual(a['exact_p'],b['exact_p'])

    def test_exposure_conversion_and_mean_comparison(self):
        a=two_poisson(713,40,515,20,length1=3,length2=6)
        b=two_poisson(713,40,515,20,length1=30,length2=60)
        for key in ('estimate','se','low','high'):self.assertAlmostEqual(a[key]/10,b[key],places=12)
        self.assertAlmostEqual(a['statistic'],b['statistic'],places=12);self.assertEqual(a['exact_p'],b['exact_p'])
        a=two_poisson(713,40,515,20,length1=3,length2=6,measure='mean')
        b=two_poisson(713,40,515,20,measure='mean')
        for key in ('estimate','se','p','exact_p'):self.assertEqual(a[key],b[key])

    def test_minitab16_help_example_only_to_displayed_precision(self):
        root=Path(__file__).parent/'fixtures/two_poisson_documentation16'
        fixture=json.loads((root/'expected.json').read_text(encoding='utf-8'))
        self.assertFalse(json.loads((root/'metadata.json').read_text(encoding='utf-8'))['executed_reference'])
        for measure in ('rate','mean'):
            r=two_poisson(**fixture['input'],measure=measure)
            for key,expected in fixture[measure].items():
                tolerance=.005 if key=='statistic' else .00005 if measure=='mean' and key=='low' else .000005
                self.assertAlmostEqual(r[key],expected,delta=tolerance)
            self.assertLess(r['p'],.0005);self.assertLess(r['exact_p'],.0005)
            self.assertGreater(r['exact_p'],0.)

    def test_zero_occurrences_confidence_only_and_nonzero_hypothesis(self):
        r=two_poisson(0,10,0,20)
        self.assertEqual(r['exact_p'],1.);self.assertIsNone(r['p']);self.assertEqual((r['low'],r['high']),(0.,0.))
        r=two_poisson(4,3,2,5,perform_test=False)
        self.assertTrue(all(r[k] is None for k in ('p','exact_p','statistic')))
        r=two_poisson(4,3,2,5,null=1)
        self.assertIsNone(r['exact_p']);self.assertIsNotNone(r['p'])
        for options in [dict(events1=-1),dict(events1=.5),dict(n1=0),dict(length1=0),dict(length2=math.inf),
                        dict(null=1,pooled=True),dict(confidence=100),dict(length1=1e308,n1=100),dict(measure='bad')]:
            values=dict(events1=4,n1=3,events2=2,n2=5);values.update(options)
            with self.subTest(options=options),self.assertRaises((ValueError,ArithmeticError)):two_poisson(**values)

    def test_summary_roundtrip_unilateral_limits_and_fixed_input(self):
        document=new_document();sheet=active_sheet(document)
        r=execute_two_poisson(sheet,input_kind='summary',summaries=[dict(events=4,n=3),dict(events=2,n=5)],alternative='greater')
        document['analyses'].append(r)
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'poisson.statlab';save_document(path,document);loaded=load_document(path)
        self.assertEqual(unpack_numbers(loaded['analyses'][0]['values'])['high'],math.inf)
        sheet=active_sheet(loaded);sync_sheet(sheet,['Other'],[['text']])
        self.assertFalse(is_stale(r,sheet));new=rerun_analysis(loaded,r['analysis_id'])
        self.assertEqual(new['values'],r['values']);self.assertEqual(new['parent_analysis_id'],r['analysis_id'])

    def test_columns_and_stacked_order_missing_and_integer_validation(self):
        document=new_document(['X','Grupo'],[['1','A'],['2','A'],['3','B'],['4','B'],['*','A'],['9','']]);sheet=active_sheet(document)
        r=execute_two_poisson(sheet,[c['id'] for c in sheet['columns']],input_kind='stacked',alternative='less')
        document['analyses'].append(r)
        self.assertEqual([s['events'] for s in r['values']['samples']],[3,7]);self.assertEqual(r['missing']['excluded_groups'],1)
        self.assertEqual(r['missing']['counts'],[1,0])
        sync_sheet(sheet,['X','Grupo'],list(reversed(sheet['rows'])))
        new=rerun_analysis(document,r['analysis_id']);self.assertEqual(new['parameters']['group_order'],['A','B'])
        self.assertEqual(new['values']['estimate'],r['values']['estimate']);validate_document(document)
        rows=deepcopy(sheet['rows']);rows[1][0]='1.5';sync_sheet(sheet,['X','Grupo'],rows)
        with self.assertRaises(ValueError):rerun_analysis(document,r['analysis_id'])


class TwoPoissonInterfaceTests(unittest.TestCase):
    def setUp(self):
        from app import MiniTaBom
        self.app=MiniTaBom();self.app.withdraw();self.addCleanup(self.app.destroy)
        self.app.headers=['A','B'];self.app.rows=[['1','3'],['2','4'],['*','']];self.app.refresh()

    def test_dialog_summary_fraction_confidence_and_navigator(self):
        dialog=self.app.two_poisson_dialog();dialog.source.current(2);dialog.toggle_source()
        for control,value in [(dialog.events[0],'713'),(dialog.ns[0],'40'),(dialog.events[1],'515'),(dialog.ns[1],'20'),(dialog.length1,'3'),(dialog.length2,'6'),(dialog.confidence,'0,95')]:
            control.delete(0,'end');control.insert(0,value)
        dialog.submit();self.assertFalse(dialog.winfo_exists())
        r=self.app.document['analyses'][-1];self.assertEqual(r['parameters']['confidence'],95.)
        self.assertAlmostEqual(r['values']['estimate'],1.65,places=12)
        self.assertTrue(any('DUAS TAXAS DE POISSON' in self.app.navigator.item(key,'text') for key in self.app.navigator.get_children('results')))

    def test_reopen_and_rerun_then_invalid_request_is_atomic(self):
        self.assertTrue(self.app.run_two_poisson(columns=[0,1]))
        old=deepcopy(self.app.document['analyses'][-1])
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'two.statlab';self.app.project_path=str(path);self.app.save_project()
            with patch('app.filedialog.askopenfilename',return_value=str(path)):self.app.open_project()
            self.assertTrue(self.app.rerun_saved_analysis(old['analysis_id']))
            self.assertEqual(self.app.document['analyses'][-1]['values'],old['values'])
        self.app.sync_document();before=deepcopy(self.app.document);text=self.app.output.get('1.0','end')
        with patch('app.messagebox.showerror'):self.assertFalse(self.app.run_two_poisson(columns=[0,1],null=1,pooled=True))
        self.assertEqual(self.app.document,before);self.assertEqual(self.app.output.get('1.0','end'),text)
