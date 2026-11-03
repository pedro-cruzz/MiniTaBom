from fractions import Fraction
import json
import math
from pathlib import Path
import unittest
from linear_models import correlations, linear_regression, format_correlation, format_regression
from inference import scientific_stats


class CorrelationTests(unittest.TestCase):
    def test_orthogonal_pair_has_zero_coefficient_unit_p_and_fisher_interval(self):
        rows = [[str(x), str(y)] for x, y in zip([1, 2, 3, 4], [1, -1, -1, 1])]
        result = correlations(['X', 'Y'], rows, [0, 1])
        pair = result['pairs'][0]
        self.assertAlmostEqual(pair['r'], 0, places=14)
        self.assertAlmostEqual(pair['p'], 1, places=14)
        expected = math.tanh(float(scientific_stats().norm.isf(.025)))
        self.assertAlmostEqual(pair['ci'][0], -expected, places=13)
        self.assertAlmostEqual(pair['ci'][1], expected, places=13)

    def test_spearman_ties_match_rounded_official_documentation_example(self):
        # Exemplo da ajuda atual, não execução nem validação do Minitab 16.
        fixture = json.loads(Path(__file__).with_name('fixtures').joinpath('spearman_documentation', 'observed.json').read_text(encoding='utf-8'))
        rows = [[str(x), str(y)] for x, y in zip(fixture['input']['first'], fixture['input']['second'])]
        result = correlations(['A', 'B'], rows, [0, 1], method='spearman')
        pair = result['pairs'][0]
        for key in fixture['displayed']:
            self.assertAlmostEqual(pair[key], fixture['displayed'][key], delta=fixture['absolute_tolerances'][key])
        self.assertIsNone(pair['ci'])

    def test_pairwise_and_listwise_omit_rows_without_shifting_pairs(self):
        rows = [['1', '1', '1'], ['2', '4', '*'], ['3', '*', '6'],
                ['4', '8', '8'], ['*', '10', '10'], ['5', '9', '11']]
        pairwise = correlations(['A', 'B', 'C'], rows, [0, 1, 2])
        listwise = correlations(['A', 'B', 'C'], rows, [0, 1, 2], missing='listwise')
        self.assertEqual([p['n'] for p in pairwise['pairs']], [4, 4, 4])
        self.assertEqual([p['n'] for p in listwise['pairs']], [3, 3, 3])
        expected = scientific_stats().pearsonr([1, 2, 4, 5], [1, 4, 8, 9])
        self.assertAlmostEqual(pairwise['pairs'][0]['r'], expected.statistic, places=13)
        self.assertAlmostEqual(pairwise['pairs'][0]['p'], expected.pvalue, places=13)

    def test_perfect_negative_pair_constant_pair_and_small_n_are_explicit(self):
        result = correlations(['A', 'B', 'C'], [['1', '-1', '7'], ['2', '-2', '7'], ['3', '-3', '7'], ['4', '-4', '7']], [0, 1, 2])
        self.assertEqual(result['pairs'][0]['r'], -1)
        self.assertEqual(result['pairs'][0]['p'], 0)
        self.assertEqual(result['pairs'][0]['ci'], (-1, -1))
        self.assertIsNone(result['pairs'][1]['r'])
        small = correlations(['A', 'B'], [['1', '2'], ['2', '4']], [0, 1])
        self.assertIsNone(small['pairs'][0]['r'])
        self.assertIn('três pares', format_correlation(small))

    def test_scale_translation_and_variable_reordering(self):
        x, y = [1, 3, 4, 6, 8], [2, 1, 7, 4, 9]
        base = correlations(['X', 'Y'], [[str(a), str(b)] for a, b in zip(x, y)], [0, 1])['pairs'][0]
        transformed = correlations(['X', 'Y'], [[str(100 - 3 * a), str(200 + 5 * b)] for a, b in zip(x, y)], [1, 0])['pairs'][0]
        self.assertAlmostEqual(transformed['r'], -base['r'], places=13)
        self.assertAlmostEqual(transformed['p'], base['p'], places=13)

    def test_invalid_options_and_original_row_context(self):
        for options in [dict(method='invalid'), dict(missing='invalid'), dict(confidence=100), dict(confidence=math.nan)]:
            with self.assertRaises(ValueError):
                correlations(['A', 'B'], [['1', '2']], [0, 1], **options)
        for columns in [[], [0], [0, 0], [0, True], [0, 4]]:
            with self.assertRaises(ValueError):
                correlations(['A', 'B'], [['1', '2']], columns)
        with self.assertRaisesRegex(ValueError, 'B: Linha 3'):
            correlations(['A', 'B'], [['1', '2'], ['*', 'nan']], [0, 1])


class RegressionTests(unittest.TestCase):
    def simple(self, confidence=95):
        return linear_regression(['X', 'Y'], [[str(x), str(y)] for x, y in zip(range(5), [1, 2, 1, 3, 5])], 1, [0], confidence=confidence)

    def test_simple_analytical_coefficients_anova_and_press(self):
        result = self.simple()
        self.assertAlmostEqual(result['terms'][0]['coefficient'], .6)
        self.assertAlmostEqual(result['terms'][1]['coefficient'], .9)
        self.assertAlmostEqual(result['ss_error'], 3.1)
        self.assertAlmostEqual(result['ss_model'], 8.1)
        self.assertAlmostEqual(result['ss_total'], 11.2)
        self.assertAlmostEqual(result['s'], math.sqrt(31 / 30))
        self.assertAlmostEqual(result['f'], 243 / 31)
        self.assertAlmostEqual(result['r2'], 100 * 81 / 112)
        self.assertAlmostEqual(result['adjusted'], 100 * 53 / 84)
        self.assertAlmostEqual(result['press'], float(5 + Fraction(34, 49) + Fraction(49, 16)))
        self.assertAlmostEqual(result['terms'][0]['se'], math.sqrt(.62))
        self.assertAlmostEqual(result['terms'][1]['se'], math.sqrt(31 / 300))
        self.assertAlmostEqual(result['terms'][1]['t'] ** 2, result['f'])

    def test_simple_matches_scipy_linregress_independent_api(self):
        result, expected = self.simple(), scientific_stats().linregress(range(5), [1, 2, 1, 3, 5])
        self.assertAlmostEqual(result['terms'][0]['coefficient'], expected.intercept, places=13)
        self.assertAlmostEqual(result['terms'][1]['coefficient'], expected.slope, places=13)
        self.assertAlmostEqual(result['terms'][1]['se'], expected.stderr, places=13)
        self.assertAlmostEqual(result['terms'][1]['p'], expected.pvalue, places=13)
        self.assertAlmostEqual(result['p'], expected.pvalue, places=13)

    def test_multiple_orthogonal_analytical_coefficients_and_diagnostics(self):
        rows = [[str(a), str(b), str(2 + 3 * a - 2 * b + .5 * a * b)] for a, b in [(-1, -1), (-1, 1), (1, -1), (1, 1)]]
        result = linear_regression(['A', 'B', 'Y'], rows, 2, [0, 1])
        for term, expected in zip(result['terms'], [2, 3, -2]):
            self.assertAlmostEqual(term['coefficient'], expected, places=13)
            self.assertAlmostEqual(term['se'], .5, places=13)
        self.assertAlmostEqual(result['f'], 26)
        self.assertAlmostEqual(result['ss_error'], 1)
        self.assertAlmostEqual(result['ss_total'], 53)
        self.assertAlmostEqual(result['press'], 16)
        for h, cook in zip(result['leverage'], result['cooks']):
            self.assertAlmostEqual(h, .75)
            self.assertAlmostEqual(cook, 1)
        for term in result['terms'][1:]:
            self.assertAlmostEqual(term['vif'], 1)

    def test_listwise_missing_retains_original_worksheet_row_numbers(self):
        rows = [['0', '1'], ['*', '5'], ['1', '2'], ['2', '*'], ['2', '1'], ['3', '3'], ['4', '5']]
        result = linear_regression(['X', 'Y'], rows, 1, [0])
        self.assertEqual(result['n'], 5)
        self.assertEqual(result['excluded'], 2)
        self.assertEqual(result['row_numbers'], [1, 3, 5, 6, 7])
        self.assertAlmostEqual(result['terms'][1]['coefficient'], .9)

    def test_scaling_translation_and_confidence_level(self):
        original = self.simple()
        transformed = linear_regression(['X', 'Y'], [[str(10 + 2 * x), str(100 - 3 * y)] for x, y in zip(range(5), [1, 2, 1, 3, 5])], 1, [0])
        self.assertAlmostEqual(transformed['terms'][1]['coefficient'], -1.35)
        self.assertAlmostEqual(transformed['terms'][0]['coefficient'], 111.7)
        self.assertAlmostEqual(transformed['ss_error'], 9 * original['ss_error'])
        self.assertAlmostEqual(transformed['r2'], original['r2'])
        self.assertAlmostEqual(transformed['press'], 9 * original['press'])
        wider = self.simple(99)
        self.assertLess(wider['terms'][1]['low'], original['terms'][1]['low'])
        self.assertGreater(wider['terms'][1]['high'], original['terms'][1]['high'])

    def test_perfect_fit_and_constant_response_have_no_invented_tests(self):
        for y in [[1 + 2 * x for x in range(5)], [7] * 5]:
            result = linear_regression(['X', 'Y'], [[str(x), str(v)] for x, v in enumerate(y)], 1, [0])
            self.assertTrue(result['perfect'])
            self.assertEqual(result['s'], 0)
            self.assertIsNone(result['f'])
            self.assertIsNone(result['terms'][1]['p'])
            self.assertEqual(result['standardized'], [None] * 5)
        self.assertIsNone(result['r2'])

    def test_unit_leverage_has_undefined_press_and_standardized_residual(self):
        result = linear_regression(['X', 'Y'], [['0', '1'], ['0', '2'], ['0', '3'], ['0', '4'], ['1', '8']], 1, [0])
        self.assertIsNone(result['press'])
        self.assertIsNone(result['predicted'])
        self.assertIsNone(result['standardized'][-1])

    def test_uninformative_model_reports_zero_adjusted_and_predicted_r_squared(self):
        result = linear_regression(['X', 'Y'], [['-1', '1'], ['0', '-2'], ['1', '1']], 1, [0])
        self.assertAlmostEqual(result['r2'], 0)
        self.assertEqual(result['adjusted'], 0)
        self.assertEqual(result['predicted'], 0)
        self.assertAlmostEqual(result['p'], 1)

    def test_press_matches_explicit_leave_one_out_refitting(self):
        scientific_stats()
        import numpy as np
        x = np.asarray([[1, 2], [2, 1], [3, 4], [5, 3], [6, 8], [8, 6]], dtype=float)
        y = np.asarray([3, 5, 4, 9, 10, 11], dtype=float)
        rows = [[str(a), str(b), str(c)] for (a, b), c in zip(x, y)]
        result = linear_regression(['A', 'B', 'Y'], rows, 2, [0, 1])
        design = np.column_stack((np.ones(len(y)), x))
        error = 0
        for i in range(len(y)):
            keep = np.arange(len(y)) != i
            coefficient = np.linalg.lstsq(design[keep], y[keep], rcond=None)[0]
            error += (y[i] - design[i] @ coefficient) ** 2
        self.assertAlmostEqual(result['press'], error, places=10)

    def test_invalid_columns_rank_constants_and_numeric_range(self):
        for response, predictors in [(0, []), (0, [0]), (0, [1, 1]), (9, [0])]:
            with self.assertRaises(ValueError):
                linear_regression(['X', 'Y'], [['1', '2']] * 5, response, predictors)
        with self.assertRaisesRegex(ValueError, 'completas'):
            linear_regression(['X', 'Y'], [['1', '2'], ['2', '3']], 1, [0])
        with self.assertRaisesRegex(ValueError, 'constantes'):
            linear_regression(['X', 'Y'], [['1', str(y)] for y in range(5)], 1, [0])
        with self.assertRaisesRegex(ValueError, 'colineares'):
            linear_regression(['A', 'B', 'Y'], [[str(x), str(2 * x), str(x + x % 2)] for x in range(5)], 2, [0, 1])
        with self.assertRaises(ValueError):
            linear_regression(['X', 'Y'], [[str(x), str(y)] for x, y in enumerate([1e308, -1e308, 1e308, -1e308])], 1, [0])

    def test_report_has_equation_anova_diagnostics_and_full_variable_names(self):
        result = self.simple()
        result['terms'][1]['label'] = 'Nome completo muito extenso da variável explicativa'
        report = format_regression(result, observations=True)
        for label in ['REGRESSÃO LINEAR', 'Análise de variância', 'PRESS', 'Alavancagem', 'Nome completo muito extenso da variável explicativa']:
            self.assertIn(label, report)


if __name__ == '__main__':
    unittest.main()
