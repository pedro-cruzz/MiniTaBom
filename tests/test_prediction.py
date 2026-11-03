import math
import unittest
from linear_models import linear_regression
from prediction import parse_cases, predict_linear, predict_columns, format_predictions
from inference import scientific_stats


class PredictionTests(unittest.TestCase):
    def model(self):
        return linear_regression(['X', 'Y'], [[str(x), str(y)] for x, y in zip(range(5), [1, 2, 1, 3, 5])], 1, [0])

    def test_at_mean_matches_analytical_standard_errors_and_intervals(self):
        model = self.model()
        case = predict_linear(model, [[2]])['cases'][0]
        critical = float(scientific_stats().t.isf(.025, 3))
        self.assertAlmostEqual(case['fit'], 2.4)
        self.assertAlmostEqual(case['leverage'], .2)
        self.assertAlmostEqual(case['se_fit'], math.sqrt(31 / 150))
        self.assertAlmostEqual(case['ci'][0], 2.4 - critical * math.sqrt(31 / 150))
        self.assertAlmostEqual(case['pi'][1], 2.4 + critical * math.sqrt(31 / 25))
        self.assertLess(case['pi'][0], case['ci'][0])
        self.assertGreater(case['pi'][1], case['ci'][1])

    def test_fitted_rows_reproduce_fits_and_leverage_without_refitting(self):
        model = self.model()
        predicted = predict_linear(model, [[x] for x in range(5)])
        for case, fit, h in zip(predicted['cases'], model['fitted'], model['leverage']):
            self.assertAlmostEqual(case['fit'], fit)
            self.assertAlmostEqual(case['leverage'], h)

    def test_multiple_model_prediction_and_outside_flags(self):
        rows = [[str(a), str(b), str(2 + 3 * a - 2 * b + .5 * a * b)] for a, b in [(-1, -1), (-1, 1), (1, -1), (1, 1)]]
        model = linear_regression(['A', 'B', 'Y'], rows, 2, [0, 1])
        mean, outside = predict_linear(model, [[0, 0], [2, 3]])['cases']
        self.assertAlmostEqual(mean['fit'], 2)
        self.assertAlmostEqual(mean['se_fit'], .5)
        self.assertEqual(mean['outside'], [])
        self.assertAlmostEqual(outside['fit'], 2)
        self.assertEqual(outside['outside'], ['A', 'B'])
        self.assertTrue(outside['high_leverage'])

    def test_one_sided_limits_and_confidence_width(self):
        model = self.model()
        both = predict_linear(model, [[2]])['cases'][0]
        lower = predict_linear(model, [[2]], alternative='lower')['cases'][0]
        upper = predict_linear(model, [[2]], alternative='upper')['cases'][0]
        wider = predict_linear(model, [[2]], confidence=99)['cases'][0]
        self.assertEqual(lower['ci'][1], math.inf)
        self.assertEqual(upper['pi'][0], -math.inf)
        self.assertGreater(lower['ci'][0], both['ci'][0])
        self.assertLess(upper['ci'][1], both['ci'][1])
        self.assertLess(wider['ci'][0], both['ci'][0])

    def test_columns_omit_missing_and_retain_worksheet_numbers(self):
        model = self.model()
        result = predict_columns(model, ['Casos'], [['2'], ['*'], ['5'], ['']], [0])
        self.assertEqual([c['case'] for c in result['cases']], [1, 3])
        self.assertEqual(result['omitted'], [2, 4])
        self.assertTrue(result['cases'][1]['outside'])
        with self.assertRaisesRegex(ValueError, 'Linha da planilha 2'):
            predict_columns(model, ['Casos'], [['2'], ['*']], [0], omit_missing=False)

    def test_input_accepts_decimal_comma_and_quotes_without_changing_data(self):
        cases, numbers = parse_cases('1,5;2\n\n"3,5";4\n', 2)
        self.assertEqual(cases, [[1.5, 2], [3.5, 4]])
        self.assertEqual(numbers, [1, 3])
        cases, _ = parse_cases('1\t2\n3\t4', 2)
        self.assertEqual(cases, [[1, 2], [3, 4]])
        for text in ['', '1', '1;*', '1;inf', '1;abc', '"1;2']:
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_cases(text, 2)

    def test_invalid_options_and_numeric_overflow_have_controlled_errors(self):
        model = self.model()
        for cases, options in [([], {}), ([[1, 2]], {}), ([[math.nan]], {}), ([[1]], {'confidence': 100}),
                               ([[1]], {'alternative': 'invalid'}), ([[1e308]], {})]:
            with self.subTest(cases=cases, options=options), self.assertRaises(ValueError):
                predict_linear(model, cases, **options)
        with self.assertRaises(ValueError):
            predict_linear({}, [[1]])

    def test_zero_residual_variance_produces_explicit_degenerate_intervals(self):
        model = linear_regression(['X', 'Y'], [[str(x), str(1 + 2 * x)] for x in range(5)], 1, [0])
        result = predict_linear(model, [[2]])
        case = result['cases'][0]
        self.assertAlmostEqual(case['fit'], 5)
        self.assertEqual(case['pi'][0], case['pi'][1])
        self.assertIn('intervalos colapsam', format_predictions(result))


if __name__ == '__main__':
    unittest.main()
