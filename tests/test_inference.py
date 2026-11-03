import math
import json
from pathlib import Path
import unittest
from inference import (one_sample, two_sample, analyze_columns, format_t_report, scientific_stats,
                       one_sample_summary, two_sample_summary, analyze_t_inputs)


class InferenceTests(unittest.TestCase):
    def test_summary_matches_raw_for_all_alternatives_and_df_policies(self):
        import statistics
        first, second = [2, 4, 5, 9, 15], [1, 2, 4, 6, 7, 8]
        summaries = [dict(n=len(v), mean=statistics.mean(v), sd=statistics.stdev(v))
                     for v in (first, second)]
        for alternative in ('two-sided', 'less', 'greater'):
            for pooled in (False, True):
                for legacy in (False, True):
                    opts = dict(alternative=alternative, equal_var=pooled, legacy_df=legacy,
                                confidence=90, null=1)
                    raw = two_sample(first, second, **opts)
                    result = two_sample_summary(*summaries, **opts)
                    for key in ('t', 'p', 'low', 'high', 'df', 'se'):
                        self.assertEqual(result[key], raw[key])

    def test_summary_analytical_cauchy_without_raw_observations(self):
        result = one_sample_summary(2, 1, math.sqrt(2))
        self.assertAlmostEqual(result['t'], 1)
        self.assertAlmostEqual(result['p'], .5, places=13)
        self.assertAlmostEqual(result['high'], 1 + math.tan(math.pi * .475), places=10)

    def test_paired_summary_requires_difference_sd(self):
        result = analyze_t_inputs([], [], 'paired', source='summary',
                                 summaries=[dict(n=3, mean=2, sd=1)])
        self.assertEqual(result['mode'], 'paired')
        self.assertEqual(result['labels'], ['Diferença'])
        self.assertEqual(len(result['samples']), 1)
        self.assertAlmostEqual(result['t'], 2 * math.sqrt(3))
        report = format_t_report(result)
        self.assertIn('resumo das diferenças', report.lower())
        self.assertIn('ausentes não informados', report)
        self.assertNotIn('Pares excluídos: 0', report)

    def test_summary_validation_and_zero_sd(self):
        for n, mean, sd in [(1, 2, 1), (True, 2, 1), (2.5, 2, 1),
                             (2147483648, 2, 1), (2, math.nan, 1), (2, 1, -1),
                             (2, 1, math.inf), (2, True, 1), (2, 1, True)]:
            with self.subTest(n=n, mean=mean, sd=sd), self.assertRaises(ValueError):
                one_sample_summary(n, mean, sd)
        with self.assertRaises(ValueError):
            one_sample_summary(3, 4, 0)
        result = two_sample_summary(dict(n=3, mean=1, sd=0), dict(n=3, mean=2, sd=1))
        self.assertEqual(result['df'], 2)
        self.assertTrue(math.isfinite(result['t']))
        for summaries in [None, [], [dict(n=3, mean=1)], [dict(n=3, mean=1, sd=1, extra=0)]]:
            with self.assertRaises(ValueError):
                analyze_t_inputs([], [], 'one', source='summary', summaries=summaries)

    def test_large_summary_and_extreme_magnitude(self):
        result = one_sample_summary(2147483647, 1, 2)
        self.assertEqual(result['df'], 2147483646)
        with self.assertRaises(ValueError):
            analyze_t_inputs([], [], 'two', source='summary',
                             summaries=[dict(n=3, mean=1e308, sd=1), dict(n=3, mean=-1e308, sd=1)])

    def test_stacked_samples_missing_groups_and_difference_order(self):
        rows = [['10', 'B'], ['1', 'A'], ['*', 'B'], ['14', 'B'],
                ['3', 'A'], ['bad value excluded', '*'], ['99', '']]
        result = analyze_t_inputs(['Resposta', 'Grupo'], rows, 'two', 0, 1,
                                  source='stacked', legacy_df=False)
        expected = two_sample([10, 14], [1, 3], legacy_df=False)
        self.assertEqual(result['estimate'], 10)
        self.assertEqual(result['missing'], [1, 0])
        self.assertEqual(result['excluded_groups'], 2)
        self.assertEqual(result['p'], expected['p'])
        self.assertIn("grupo 'B'", result['labels'][0])
        self.assertIn('primeira aparição', format_t_report(result))
        reversed_result = analyze_t_inputs(['Resposta', 'Grupo'], rows[1:] + rows[:1], 'two', 0, 1,
                                           source='stacked', legacy_df=False)
        self.assertEqual(reversed_result['estimate'], -10)
        self.assertEqual(reversed_result['p'], result['p'])

    def test_invalid_stacked_layout_and_group_count(self):
        for mode, first, second, rows in [
                ('one', 0, 1, [['1', 'A']]), ('two', 0, 0, [['1', 'A']]),
                ('two', 0, 1, [['1', 'A'], ['2', 'B'], ['3', 'C']]),
                ('two', 0, 1, [['1', 'A'], ['2', 'A']])]:
            with self.assertRaises(ValueError):
                analyze_t_inputs(['Resposta', 'Grupo'], rows, mode, first, second, source='stacked')

    def test_observed_minitab_22_6_rounded_output(self):
        fixture = json.loads(Path(__file__).with_name('fixtures').joinpath('welch_minitab_22_6', 'observed.json').read_text(encoding='utf-8'))
        result = two_sample(fixture['input']['first'], fixture['input']['second'], **fixture['options'])
        for key, expected in fixture['displayed'].items():
            with self.subTest(key=key):
                self.assertAlmostEqual(result[key], expected, delta=fixture['absolute_tolerances'][key])

    def test_two_point_sample_has_exact_cauchy_probability(self):
        result = one_sample([0, 2])
        self.assertEqual(result['estimate'], 1)
        self.assertEqual(result['df'], 1)
        self.assertAlmostEqual(result['t'], 1)
        self.assertAlmostEqual(result['p'], .5, places=13)
        # t(1) é Cauchy: quantil = tan(pi * (p - 1/2)).
        margin = math.tan(math.pi * (.975 - .5))
        self.assertAlmostEqual(result['low'], 1 - margin, places=10)
        self.assertAlmostEqual(result['high'], 1 + margin, places=10)

    def test_one_sided_bounds_and_confidence_only_format(self):
        upper = one_sample([0, 2], alternative='less')
        lower = one_sample([0, 2], alternative='greater')
        self.assertAlmostEqual(upper['p'], .75)
        self.assertAlmostEqual(lower['p'], .25)
        self.assertEqual(upper['low'], -math.inf)
        self.assertEqual(lower['high'], math.inf)
        self.assertAlmostEqual(lower['low'], 1 - math.tan(math.pi * .45), places=10)
        result = analyze_columns(['X'], [['0'], ['2']], 'one', 0)
        report = format_t_report(result, perform_test=False)
        self.assertIn('IC de 95%', report)
        self.assertNotIn('Valor-p', report)

    def test_welch_and_pooled_match_independent_scipy_test_api(self):
        stats = scientific_stats()
        first, second = [2, 4, 5, 9, 15], [1, 2, 4, 6, 7, 8]
        for pooled in (True, False):
            for alternative in ('two-sided', 'less', 'greater'):
                with self.subTest(pooled=pooled, alternative=alternative):
                    result = two_sample(first, second, equal_var=pooled, legacy_df=False, alternative=alternative)
                    expected = stats.ttest_ind(first, second, equal_var=pooled, alternative=alternative)
                    self.assertAlmostEqual(result['t'], expected.statistic, places=12)
                    self.assertAlmostEqual(result['p'], expected.pvalue, places=12)
                    self.assertAlmostEqual(result['df'], expected.df, places=12)

    def test_legacy_welch_floors_df_and_widens_interval(self):
        first, second = [2, 4, 5, 9, 15], [1, 2, 4, 6, 7, 8]
        modern = two_sample(first, second, legacy_df=False)
        legacy = two_sample(first, second, legacy_df=True)
        self.assertEqual(legacy['df'], math.floor(modern['df']))
        self.assertLess(legacy['low'], modern['low'])
        self.assertGreater(legacy['high'], modern['high'])
        self.assertEqual(legacy['t'], modern['t'])

    def test_legacy_df_does_not_truncate_floating_roundoff(self):
        for n in range(2, 31):
            with self.subTest(n=n):
                result = two_sample(list(range(n)), list(range(n)), legacy_df=True)
                self.assertEqual(result['df'], 2 * n - 2)

    def test_paired_omits_pairs_instead_of_shifting_rows(self):
        rows = [['10', '1'], ['*', '100'], ['20', '*'], ['30', '3'], ['40', '5']]
        result = analyze_columns(['Antes', 'Depois'], rows, 'paired', 0, 1)
        self.assertEqual(result['missing'], [2])
        self.assertEqual(result['samples'][0]['n'], 3)
        expected = one_sample([9, 27, 35])
        self.assertAlmostEqual(result['t'], expected['t'])
        self.assertAlmostEqual(result['estimate'], 71 / 3)
        self.assertIn('Pares excluídos: 2', format_t_report(result))

    def test_independent_missing_and_nonzero_null(self):
        result = analyze_columns(['A', 'B'], [['1,5', '4'], ['*', '6'], ['3,5', '8']],
                                 'two', 0, 1, null=-3.5, legacy_df=False)
        self.assertEqual([sample['n'] for sample in result['samples']], [2, 3])
        self.assertEqual(result['missing'], [1, 0])
        self.assertAlmostEqual(result['t'], 0)
        self.assertAlmostEqual(result['p'], 1)

    def test_invalid_inputs_produce_controlled_errors(self):
        for values in ([], [1], [2, 2], [float('nan'), 1], [-1e308, 1e308]):
            with self.subTest(values=values), self.assertRaises(ValueError):
                analyze_columns(['A'], [[str(v)] for v in values], 'one', 0)
        for options in (dict(confidence=100), dict(confidence=0), dict(confidence=math.nan),
                        dict(null=math.inf), dict(alternative='bad')):
            with self.assertRaises(ValueError):
                one_sample([1, 2, 3], **options)
        with self.assertRaisesRegex(ValueError, 'duas colunas diferentes'):
            analyze_columns(['A'], [['1'], ['2']], 'paired', 0, 0)
        with self.assertRaisesRegex(ValueError, 'Linha 3, B'):
            analyze_columns(['A', 'B'], [['1', '2'], ['*', 'abc']], 'paired', 0, 1)

    def test_one_constant_group_is_allowed_when_standard_error_positive(self):
        result = two_sample([1, 1, 1], [1, 2, 3], legacy_df=False)
        self.assertTrue(math.isfinite(result['t']))
        self.assertAlmostEqual(result['df'], 2)


if __name__ == '__main__':
    unittest.main()
