import math
import unittest

from extended_inference import (two_proportions, one_variance, two_variances,
                                 analyze_extended, format_extended)


class ExtendedInferenceTests(unittest.TestCase):
    def test_two_proportions_separate_and_pooled_analytic(self):
        r = two_proportions(30, 100, 20, 100)
        se = math.sqrt(.3 * .7 / 100 + .2 * .8 / 100)
        self.assertAlmostEqual(r['estimate'], .1)
        self.assertAlmostEqual(r['statistic'], .1 / se)
        self.assertAlmostEqual(r['p'], math.erfc(.1 / se / math.sqrt(2)))
        self.assertAlmostEqual(r['low'], .1 - 1.959963984540054 * se)
        pooled = two_proportions(30, 100, 20, 100, pooled=True)
        self.assertAlmostEqual(pooled['statistic'], .1 / math.sqrt(.25 * .75 * .02))
        self.assertEqual((pooled['low'], pooled['high']), (r['low'], r['high']))
        nonzero = two_proportions(30, 100, 20, 100, null=.1)
        self.assertAlmostEqual(nonzero['p'], 1)
        self.assertIsNone(nonzero['fisher'])

    def test_fisher_independent_hypergeometric_enumeration_and_tails(self):
        # [[6, 2], [1, 4]]; enumeração por combinações, sem chamar SciPy.
        denominator = math.comb(13, 8)
        probabilities = {x: math.comb(7, x) * math.comb(6, 8 - x) / denominator for x in range(2, 8)}
        expected = sum(p for p in probabilities.values() if p <= probabilities[6] + 1e-14)
        r = two_proportions(6, 8, 1, 5)
        self.assertAlmostEqual(r['fisher'], expected, places=14)
        self.assertAlmostEqual(two_proportions(6, 8, 1, 5, alternative='less')['fisher'],
                               sum(p for x, p in probabilities.items() if x <= 6))
        self.assertAlmostEqual(two_proportions(6, 8, 1, 5, alternative='greater')['fisher'],
                               sum(p for x, p in probabilities.items() if x >= 6))
        lower = two_proportions(30, 100, 20, 100, alternative='greater')
        upper = two_proportions(30, 100, 20, 100, alternative='less')
        self.assertEqual((lower['high'], upper['low']), (1, -1))
        self.assertAlmostEqual(lower['p'] + upper['p'], 1)

    def test_proportion_boundaries_report_unavailable_and_wald_limits(self):
        zero = two_proportions(0, 10, 0, 12)
        self.assertIsNone(zero['p'])
        self.assertEqual((zero['fisher'], zero['low'], zero['high']), (1, 0, 0))
        extreme = two_proportions(1, 1, 0, 1, pooled=True)
        self.assertIsNotNone(extreme['p'])
        self.assertEqual((extreme['low'], extreme['high']), (1, 1))
        r = two_proportions(1, 2, 0, 1)
        self.assertGreater(r['high'], 1)
        report = format_extended(zero)
        self.assertIn('indisponível', report)
        self.assertIn('IC Wald degenerado', report)
        ci_only = format_extended(zero, False)
        self.assertNotIn('Valor-p', ci_only)
        self.assertNotIn('Teste Z indisponível', ci_only)
        self.assertNotIn('H0:', ci_only)
        huge = two_proportions(900_000, 2_000_000, 800_000, 2_000_000)
        self.assertIsNone(huge['fisher'])
        self.assertIsNotNone(huge['p'])
        self.assertIn('limite operacional', format_extended(huge))
        extreme = two_proportions(0, 1_000_000, 1_000_000, 1_000_000, pooled=True)
        self.assertEqual(extreme['p'], 0)
        self.assertIn('Valor-p normal < 0,000001', format_extended(extreme))

    def test_one_variance_closed_chi_square_df2(self):
        # X²(2): CDF(x)=1−exp(−x/2), quantil(p)=−2ln(1−p).
        r = one_variance(3, 4, null=4, measure='variance')
        self.assertEqual((r['statistic'], r['df']), (2, [2]))
        self.assertAlmostEqual(r['p'], 2 * math.exp(-1))
        self.assertAlmostEqual(r['low'], 8 / (-2 * math.log(.025)))
        self.assertAlmostEqual(r['high'], 8 / (-2 * math.log(.975)))
        sd = one_variance(3, 2, null=2)
        self.assertAlmostEqual(sd['low'] ** 2, r['low'])
        self.assertAlmostEqual(sd['high'] ** 2, r['high'])
        self.assertEqual(sd['p'], r['p'])
        for alternative in ('less', 'greater'):
            s = one_variance(3, 4, null=4, measure='variance', alternative=alternative)
            self.assertAlmostEqual(s['p'], 1 - math.exp(-1) if alternative == 'less' else math.exp(-1))
            self.assertEqual(s['low'] if alternative == 'less' else s['high'], 0 if alternative == 'less' else math.inf)

    def test_two_variances_closed_f_df2_and_sd_ratio(self):
        # F(2,2): CDF(x)=x/(1+x); quantil(p)=p/(1−p).
        r = two_variances(3, 8, 3, 2, measure='variance')
        self.assertEqual((r['statistic'], r['df'], r['estimate']), (4, [2, 2], 4))
        self.assertAlmostEqual(r['p'], .4)
        self.assertAlmostEqual(r['low'], 4 / 39)
        self.assertAlmostEqual(r['high'], 4 * 39)
        sd = two_variances(3, math.sqrt(8), 3, math.sqrt(2), null=2)
        self.assertAlmostEqual(sd['statistic'], 1)
        self.assertAlmostEqual(sd['p'], 1)
        self.assertAlmostEqual(sd['low'] ** 2, r['low'])
        self.assertAlmostEqual(sd['high'] ** 2, r['high'])

    def test_variance_swap_reciprocity_and_one_sided(self):
        a = two_variances(8, 4, 13, 2)
        b = two_variances(13, 2, 8, 4)
        self.assertAlmostEqual(a['p'], b['p'])
        self.assertAlmostEqual(a['low'], 1 / b['high'])
        self.assertAlmostEqual(a['high'], 1 / b['low'])
        less = two_variances(8, 4, 13, 2, alternative='less')
        greater = two_variances(8, 4, 13, 2, alternative='greater')
        self.assertAlmostEqual(less['p'] + greater['p'], 1)
        self.assertEqual((less['low'], greater['high']), (0, math.inf))
        self.assertLess(less['high'], a['high'])
        self.assertGreater(greater['low'], a['low'])

    def test_columns_and_stacked_omit_independently_with_explicit_order(self):
        rows = [['1', '3'], ['*', '5'], ['3', ''], ['5', '7']]
        r = analyze_extended(['A', 'B'], rows, 'two_variances', [0, 1])
        self.assertEqual([s['n'] for s in r['samples']], [3, 3])
        self.assertEqual([s['missing'] for s in r['samples']], [1, 1])
        self.assertEqual(r['estimate'], 1)
        stacked = [['1', ' B '], ['2', 'A'], ['3', 'B'], ['*', 'B'],
                   ['6', 'A'], ['7', 'B'], ['nan', '']]
        s = analyze_extended(['Y', 'G'], stacked, 'two_variances', [0], source='stacked', group=1)
        self.assertIn("'B'", s['samples'][0]['name'])
        self.assertEqual((s['excluded_groups'], s['samples'][0]['missing']), (1, 1))
        self.assertEqual([sample['n'] for sample in s['samples']], [3, 2])
        single = analyze_extended(['A', 'B'], rows, 'one_variance', [0])
        self.assertEqual(single['samples'][0]['variance'], 4)

    def test_proportion_columns_encoding_events_and_stacked_equivalence(self):
        rows = [['Sim', '1'], ['Não', '0'], ['Sim', '*'], ['', '1']]
        r = analyze_extended(['A', 'B'], rows, 'two_proportions', [0, 1], events=['Sim', '1'])
        self.assertEqual([s['events'] for s in r['samples']], [2, 2])
        self.assertEqual([s['n'] for s in r['samples']], [3, 3])
        stacked = [['Sim', 'B'], ['Sim', 'A'], ['Não', 'B'], ['Sim', 'A'], ['Sim', 'B'],
                   ['Não', 'A'], ['*', 'B'], ['', 'A']]
        s = analyze_extended(['Y', 'G'], stacked, 'two_proportions', [0], source='stacked', group=1, events=['Sim'] * 2)
        self.assertEqual((s['p'], s['fisher']), (r['p'], r['fisher']))
        zero = analyze_extended(['A', 'B'], [['Não', 'Não']], 'two_proportions', [0, 1], events=['Sim'] * 2)
        self.assertEqual([sample['events'] for sample in zero['samples']], [0, 0])

    def test_invalid_domains_and_numeric_precision(self):
        cases = [lambda: two_proportions(3, 2, 1, 5), lambda: two_proportions(True, 2, 1, 5),
                 lambda: two_proportions(1, 2, 1, 5, null=.1, pooled=True),
                 lambda: two_proportions(1, 2, 1, 5, null=2),
                 lambda: one_variance(1, 2), lambda: one_variance(3, 0), lambda: one_variance(3, 1, null=0),
                 lambda: one_variance(3, 1, measure='unknown'), lambda: one_variance(3, 1e308),
                 lambda: one_variance(3, 5e-324), lambda: two_variances(3, 1, 3, 0),
                 lambda: two_variances(3, 1e150, 3, 1e-150),
                 lambda: one_variance(3, 1, confidence=100), lambda: two_variances(3, 1, 3, 1, alternative='bad')]
        for case in cases:
            with self.subTest(case=case), self.assertRaises(ValueError):
                case()
        for rows, mode, columns, kwargs in [
            ([['nan', '2'], ['1', '3']], 'two_variances', [0, 1], {}),
            ([['1', '2'], ['1', '3']], 'two_variances', [0, 1], {}),
            ([['A', 'A'], ['B', 'B'], ['C', 'A']], 'two_proportions', [0, 1], {'events': ['A', 'A']}),
            ([['A', 'A'], ['B', 'B']], 'two_proportions', [0, 1], {'events': ['C', 'A']}),
            ([['1', 'G']], 'two_variances', [0], {'source': 'stacked', 'group': 1}),
            ([['1', 'A'], ['2', 'B'], ['3', 'C']], 'two_variances', [0], {'source': 'stacked', 'group': 1}),
            ([['1', '2']], 'two_variances', [0, 0], {}),
        ]:
            with self.subTest(rows=rows, mode=mode), self.assertRaises(ValueError):
                analyze_extended(['A', 'B'], rows, mode, columns, **kwargs)


if __name__ == '__main__':
    unittest.main()
