import math
import unittest
import warnings

from inference import scientific_stats
from normality import normality_test, analyze_normality, ad_probability, format_normality


class NormalityTests(unittest.TestCase):
    def test_statistic_against_scipy_for_symmetric_skew_and_tied_samples(self):
        for sample in ([-2, -1, 0, 1, 2], [1, 2, 3, 4, 5, 6, 7, 20], [1, 1, 1, 2, 2, 3, 5, 9]):
            with self.subTest(sample=sample):
                r = normality_test(sample)
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore', FutureWarning)
                    expected = scientific_stats().anderson(sample, dist='norm').statistic
                self.assertAlmostEqual(r['statistic'], expected, places=13)
                self.assertTrue(0 <= r['p'] <= 1)

    def test_three_points_independent_closed_statistic_and_probability(self):
        # [-1,0,1] tem média 0, desvio amostral 1.
        phi = .5 * math.erfc(1 / math.sqrt(2))
        statistic = -3 - (2 * math.log(phi) + 6 * math.log(.5) + 10 * math.log(1 - phi)) / 3
        r = normality_test([-1, 0, 1])
        self.assertAlmostEqual(r['statistic'], statistic, places=14)
        a = statistic * (1 + .75/3 + 2.25/9)
        self.assertTrue(.2 <= a < .34)
        expected_p = 1 - math.exp(-8.318 + 42.796 * a - 59.938 * a*a)
        self.assertAlmostEqual(r['p'], expected_p, places=14)

    def test_probability_branches_boundaries_and_large_statistic_bound(self):
        equations = [(0.1, lambda a: 1 - math.exp(-13.436 + 101.14*a - 223.73*a*a)),
                     (.2, lambda a: 1 - math.exp(-8.318 + 42.796*a - 59.938*a*a)),
                     (.34, lambda a: math.exp(.9177 - 4.279*a - 1.38*a*a)),
                     (.6, lambda a: math.exp(1.2937 - 5.709*a + .0186*a*a)),
                     (13, lambda a: math.exp(1.2937 - 5.709*a + .0186*a*a))]
        for a, equation in equations:
            self.assertAlmostEqual(ad_probability(a)[0], equation(a), places=14)
        r = normality_test([0] * 199 + [10])
        self.assertGreater(r['adjusted'], 13)
        self.assertIsNone(r['p'])
        self.assertGreater(r['p_upper'], 0)
        self.assertIn('Valor-p aproximado <', format_normality(r))

    def test_affine_invariance_extreme_finite_data_and_missing(self):
        sample = [-2, -1, 0, 1, 2, 4]
        original = normality_test(sample)
        for transformed in ([7 + 3*x for x in sample], [-x for x in sample],
                            [x * 1e-250 for x in sample], [x * 1e307 for x in sample]):
            self.assertAlmostEqual(normality_test(transformed)['statistic'], original['statistic'], places=12)
        r = analyze_normality(['Medição'], [['1,5'], ['*'], [''], ['2,5'], ['3,5']], 0)
        self.assertEqual((r['n'], r['missing'], r['source']), (3, 2, 'Medição'))
        self.assertIn('Amostra pequena', format_normality(r))

    def test_invalid_samples_constants_and_nonfinite(self):
        for values in ([], [1, 2], [1, 1, 1], [1, 2, math.nan], [1, 2, math.inf],
                       [1, 2, 3] * 70_000):
            with self.subTest(n=len(values)), self.assertRaises(ValueError):
                normality_test(values)
        for a in (-1, math.inf, math.nan):
            with self.assertRaises(ValueError):
                ad_probability(a)
        with self.assertRaises(ValueError):
            analyze_normality(['A'], [['1'], ['2'], ['texto']], 0)


if __name__ == '__main__':
    unittest.main()
