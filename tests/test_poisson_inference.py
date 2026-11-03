import math
import unittest
from unittest.mock import patch

from poisson_inference import one_poisson, analyze_poisson, format_poisson, poisson_exact_p


class PoissonTests(unittest.TestCase):
    @staticmethod
    def probability(k, mean):
        return math.exp(-mean) * mean ** k / math.factorial(k)

    def test_likelihood_ratio_p_against_direct_enumeration(self):
        # Independent finite sum, with omitted Poisson tail < 1e-25.
        for mean in (.1, .75, 1., 2.5, 5., 9.):
            for observed in (0, 1, 3, 8, 15):
                target = observed * math.log(observed / mean) - observed + mean if observed else mean
                expected = 0.
                for k in range(100):
                    distance = k * math.log(k / mean) - k + mean if k else mean
                    if distance >= target - 1e-11:
                        expected += self.probability(k, mean)
                self.assertAlmostEqual(poisson_exact_p(observed, mean), expected, places=12)

    def test_inclusive_unilateral_and_mle(self):
        self.assertAlmostEqual(poisson_exact_p(2, 3, 'less'), math.exp(-3) * (1+3+4.5))
        self.assertAlmostEqual(poisson_exact_p(2, 3, 'greater'), 1-math.exp(-3)*4)
        self.assertEqual(poisson_exact_p(3, 3), 1.)

    def test_likelihood_is_not_twice_the_smallest_tail(self):
        p = poisson_exact_p(0, 1)
        expected = math.exp(-1) + 1 - math.exp(-1) * 2.5  # opposite tail begins at 3
        self.assertAlmostEqual(p, expected)
        self.assertNotAlmostEqual(p, 2 * math.exp(-1))

    def test_zero_count_garwood_upper_bound(self):
        result = one_poisson(0, 10)
        self.assertEqual(result['low'], 0)
        self.assertAlmostEqual(result['high'], -math.log(.025)/10)
        lower = one_poisson(0, 10, alternative='less')
        self.assertAlmostEqual(lower['high'], -math.log(.05)/10)
        self.assertEqual(one_poisson(0, 10, alternative='greater')['high'], math.inf)

    def test_exact_interval_inverts_equal_inclusive_tails(self):
        result = one_poisson(3, 4, length=2.)
        lower_mean, upper_mean = result['low']*8, result['high']*8
        self.assertAlmostEqual(1-sum(self.probability(k,lower_mean) for k in range(3)), .025, places=12)
        self.assertAlmostEqual(sum(self.probability(k,upper_mean) for k in range(4)), .025, places=12)

    def test_unit_conversion_preserves_hypothesis_test(self):
        first = one_poisson(15, 10, null=2)
        second = one_poisson(15, 10, length=100, null=.02)
        self.assertEqual(first['p'], second['p'])
        for key in ('estimate','se','low','high'):
            self.assertAlmostEqual(first[key]/100, second[key])

    def test_normal_uses_observed_variance(self):
        result = one_poisson(25, 5, null=3, method='normal')
        self.assertEqual(result['estimate'],5.)
        self.assertEqual(result['statistic'],2.)
        self.assertAlmostEqual(result['p'],math.erfc(math.sqrt(2)))
        self.assertAlmostEqual(result['high']-result['estimate'],1.959963984540054, places=10)

    def test_normal_zero_has_no_test_and_explicit_warning(self):
        result=one_poisson(0,10,method='normal')
        self.assertIsNone(result['p'])
        self.assertEqual(result['low'],result['high'])
        self.assertIn('indisponível',format_poisson(result))
        self.assertIn('degenerado',format_poisson(result))

    def test_zero_null_degenerate_distribution(self):
        self.assertEqual(one_poisson(0,10,null=0)['p'],1)
        self.assertEqual(one_poisson(1,10,null=0)['p'],0)
        self.assertEqual(one_poisson(1,10,null=0,alternative='less')['p'],1)

    def test_raw_counts_missing_and_summary_equivalence(self):
        raw=analyze_poisson(['Calls'],[['0'],['1'],['*'],[''],['2,0']],0,length=3)
        summary=one_poisson(3,3,length=3)
        self.assertEqual(raw['missing'],2)
        for key in ('estimate','low','high','p'):self.assertEqual(raw[key],summary[key])
        for invalid in ('-1','.5','nan','x'):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                analyze_poisson(['X'],[[invalid]],0)

    def test_reject_invalid_parameters(self):
        for options in ({'events':-1},{'events':True},{'events':.5},{'n':0},{'length':0},
                        {'length':math.inf},{'null':-1},{'confidence':100},{'method':'other'},
                        {'alternative':'bad'},{'null':1e300},{'length':1e-320}):
            values=dict(events=2,n=10);values.update(options)
            with self.subTest(options=options), self.assertRaises((ValueError,ArithmeticError)):
                one_poisson(**values)

    def test_large_mean_uses_integer_search(self):
        self.assertEqual(one_poisson(1_000_000_000,1,null=1e9)['p'],1.)
        result=one_poisson(999_900_000,1,null=1e9)
        self.assertTrue(0<result['p']<.01)

    def test_interval_only_report_omits_hypothesis(self):
        report=format_poisson(one_poisson(5,10),perform_test=False)
        self.assertIn('IC de 95%',report)
        self.assertNotIn('H0:',report)
        self.assertNotIn('Valor-p',report)


class PoissonInterfaceTests(unittest.TestCase):
    def setUp(self):
        from app import MiniTaBom
        self.app=MiniTaBom();self.app.withdraw()
        self.app.headers=['Contagens'];self.app.rows=[['0'],['1'],['2'],['*']]
        self.app.refresh_table()

    def tearDown(self):self.app.destroy()

    def test_column_dialog_and_navigator(self):
        dialog=self.app.poisson_dialog();dialog.submit()
        self.assertFalse(dialog.winfo_exists())
        self.assertIn('Ocorrências = 3',self.app.output.get('1.0','end'))
        self.assertTrue(any('TAXA DE POISSON' in self.app.navigator.item(key,'text')
                            for key in self.app.navigator.get_children('results')))

    def test_summary_options_and_failure_atomicity(self):
        dialog=self.app.poisson_dialog();dialog.source.current(1);dialog.toggle_source()
        dialog.events.delete(0,'end');dialog.events.insert(0,'25')
        dialog.method.current(1);dialog.perform_test.set(False);dialog.toggle_test()
        dialog.submit()
        self.assertFalse(dialog.winfo_exists())
        self.assertNotIn('H0:',self.app.output.get('1.0','end'))
        before=self.app.output.get('1.0','end')
        with patch('app.messagebox.showerror'):
            self.assertFalse(self.app.run_poisson('summary',events=-1,n=10))
        self.assertEqual(before,self.app.output.get('1.0','end'))
