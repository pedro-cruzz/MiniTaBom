import math
import unittest

from basic_inference import analyze_basic, z_mean, one_proportion, format_basic, parse_count
from inference import scientific_stats


class BasicInferenceTests(unittest.TestCase):
    def test_z_known_closed_case_and_tails(self):
        r = z_mean(25, 12, 5, null=10)
        self.assertEqual((r['estimate'], r['se'], r['statistic']), (12, 1, 2))
        self.assertAlmostEqual(r['p'], .0455002638963584, places=14)
        self.assertAlmostEqual(r['low'], 10.040036015459946, places=12)
        self.assertAlmostEqual(r['high'], 13.959963984540054, places=12)
        self.assertGreater(z_mean(2, 10, math.sqrt(2))['p'], 0)
        self.assertLess(z_mean(2, 10, math.sqrt(2))['p'], 2e-23)

    def test_z_one_sided_and_column_missing_constants(self):
        greater = z_mean(4, 1, 2, alternative='greater')
        less = z_mean(4, 1, 2, alternative='less')
        self.assertAlmostEqual(greater['p'], .15865525393145707)
        self.assertAlmostEqual(greater['low'], -.6448536269514722)
        self.assertEqual(greater['high'], math.inf)
        self.assertEqual(less['low'], -math.inf)
        self.assertAlmostEqual(less['high'], 2.6448536269514722)
        self.assertAlmostEqual(less['p'] + greater['p'], 1)
        r = analyze_basic(['A'], [['1,5'], ['*'], [''], ['1,5']], 'z', 0, sigma=2, null=1.5)
        self.assertEqual((r['n'], r['missing'], r['p']), (2, 2, 1))
        self.assertEqual(r['source'], 'A')

    def test_z_invalid_inputs_and_precision(self):
        for options in [dict(n=1), dict(n=True), dict(n=3.), dict(sigma=0), dict(sigma=-1),
                        dict(sigma=math.inf), dict(mean=math.nan), dict(null=math.inf),
                        dict(confidence=0), dict(confidence=100), dict(alternative='invalid'),
                        dict(mean=1e308, null=-1e308), dict(sigma=5e-324, n=100)]:
            args = dict(n=4, mean=0, sigma=1)
            args.update(options)
            with self.subTest(options=options), self.assertRaises(ValueError):
                z_mean(**args)
        with self.assertRaisesRegex(ValueError, 'A:'):
            analyze_basic(['A'], [['a'], ['2']], 'z', 0, sigma=1)

    def test_exact_p_values_against_enumerated_binomial_probabilities(self):
        for n in (1, 7, 12):
            for k in range(n + 1):
                p0 = .3
                probabilities = [math.comb(n, j) * p0 ** j * (1 - p0) ** (n - j) for j in range(n + 1)]
                low, high = sum(probabilities[:k + 1]), sum(probabilities[k:])
                for alternative, expected in [('less', low), ('greater', high), ('two-sided', min(1., 2 * min(low, high)))]:
                    r = one_proportion(k, n, null=p0, alternative=alternative)
                    self.assertAlmostEqual(r['p'], expected, places=13)

    def test_exact_boundaries_closed_form_and_one_sided_limits(self):
        for confidence in (80, 95, 99):
            alpha = 1 - confidence / 100
            none = one_proportion(0, 10, confidence=confidence)
            all_events = one_proportion(10, 10, confidence=confidence)
            self.assertEqual(none['low'], 0)
            self.assertAlmostEqual(none['high'], 1 - (alpha / 2) ** .1)
            self.assertEqual(all_events['high'], 1)
            self.assertAlmostEqual(all_events['low'], (alpha / 2) ** .1)
            one_side = one_proportion(0, 10, confidence=confidence, alternative='less')
            self.assertEqual(one_side['low'], 0)
            self.assertAlmostEqual(one_side['high'], 1 - alpha ** .1)
        self.assertEqual(one_proportion(0, 5, null=0)['p'], 1)
        self.assertEqual(one_proportion(1, 5, null=0)['p'], 0)
        self.assertEqual(one_proportion(5, 5, null=1)['p'], 1)
        self.assertEqual(one_proportion(4, 5, null=1, alternative='greater')['p'], 1)

    def test_exact_ci_inverts_equal_tailed_test_and_nests(self):
        r = one_proportion(7, 50, null=.1)
        self.assertAlmostEqual(r['low'], .05819170033997342, places=11)
        self.assertAlmostEqual(r['high'], .26739600249700846, places=11)
        for bound in ('low', 'high'):
            at_bound = one_proportion(7, 50, null=r[bound])
            self.assertAlmostEqual(at_bound['p'], .05, places=10)
        wide = one_proportion(7, 50, confidence=99)
        self.assertLess(wide['low'], r['low'])
        self.assertGreater(wide['high'], r['high'])

    def test_wilson_matches_independent_reference_and_score_null_variance(self):
        stats = scientific_stats()
        for n, k in [(1, 0), (1, 1), (20, 4), (20, 20), (100, 87)]:
            for alternative in ('two-sided', 'less', 'greater'):
                with self.subTest(n=n, k=k, alternative=alternative):
                    r = one_proportion(k, n, null=.2, method='score', alternative=alternative)
                    ci = stats.binomtest(k, n, alternative=alternative).proportion_ci(method='wilson')
                    self.assertAlmostEqual(r['low'], ci.low, places=13)
                    self.assertAlmostEqual(r['high'], ci.high, places=13)
                    self.assertAlmostEqual(r['statistic'], (k / n - .2) / math.sqrt(.16 / n))

    def test_wald_uncropped_and_degenerate_intervals_are_explicit(self):
        r = one_proportion(1, 10, method='wald')
        self.assertLess(r['low'], 0)
        self.assertIn('pode ultrapassar', format_basic(r))
        r = one_proportion(10, 10, method='wald')
        self.assertEqual((r['low'], r['high']), (1, 1))
        self.assertAlmostEqual(r['p'], one_proportion(10, 10, method='score')['p'])

    def test_categorical_event_missing_and_single_level_cases(self):
        r = analyze_basic(['Compra'], [['Sim'], ['Não'], [' Sim '], ['*'], ['']],
                          'proportion', 0, event='Sim')
        self.assertEqual((r['n'], r['events'], r['missing']), (3, 2, 2))
        self.assertEqual(r['event'], 'Sim')
        r = analyze_basic(['Compra'], [['Não'], ['Não']], 'proportion', 0, event='Sim')
        self.assertEqual((r['events'], r['n']), (0, 2))
        for values, event in [(['Sim', 'Não'], 'sim'), (['Sim', 'Não', 'Talvez'], 'Sim'), (['*', ''], 'Sim'), (['Sim'], '*')]:
            with self.subTest(values=values), self.assertRaises(ValueError):
                analyze_basic(['Compra'], [[v] for v in values], 'proportion', 0, event=event)

    def test_proportion_invalid_options_and_exact_count_parser(self):
        self.assertEqual(parse_count('20,0'), 20)
        self.assertEqual(parse_count('2e2'), 200)
        for value in ('1.5', 'NaN', '-1', '2147483648', '1e999999', ''):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_count(value)
        for options in [dict(n=0), dict(n=True), dict(events=-1), dict(events=11), dict(events=2.),
                        dict(null=-.1), dict(null=math.nan), dict(method='unknown'),
                        dict(method='score', null=0), dict(method='wald', null=1), dict(confidence=100),
                        dict(method='score', null=5e-324, n=2_147_483_647),
                        dict(method='wald', events=9, n=10, alternative='greater', confidence=10)]:
            args = dict(events=2, n=10)
            args.update(options)
            with self.subTest(options=options), self.assertRaises(ValueError):
                one_proportion(**args)

    def test_reports_omit_test_when_requested_and_keep_interval(self):
        for r in (z_mean(10, 1, 2), one_proportion(3, 10)):
            text = format_basic(r, False)
            self.assertIn('IC de 95%', text)
            self.assertNotIn('H0:', text)
            self.assertNotIn('Valor-p', text)
            self.assertNotIn('Teste binomial', text)
        self.assertIn('−∞', format_basic(z_mean(10, 1, 2, alternative='less')))


if __name__ == '__main__':
    unittest.main()
