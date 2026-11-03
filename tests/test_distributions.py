import math
import unittest
from distributions import DISTRIBUTIONS, distribution_calculation, frozen_distribution, format_distribution


class DistributionTests(unittest.TestCase):
    def value(self, name, params, operation, x, upper=None):
        return distribution_calculation(name, params, operation, x, upper)['result']

    def test_normal_and_cauchy_analytical_values(self):
        normal = dict(mean=0, sd=1)
        self.assertEqual(self.value('Normal', normal, 'cdf', 0), .5)
        self.assertAlmostEqual(self.value('Normal', normal, 'density', 0), 1 / math.sqrt(2 * math.pi))
        self.assertAlmostEqual(self.value('t de Student', {'df': 1}, 'density', 0), 1 / math.pi)
        self.assertAlmostEqual(self.value('t de Student', {'df': 1}, 'cdf', 1), .75)
        self.assertAlmostEqual(self.value('t de Student', {'df': 1}, 'quantile', .75), 1)
        tail = self.value('Normal', normal, 'sf', 10)
        interval = self.value('Normal', normal, 'interval', 10, 11)
        self.assertGreater(interval, 0)
        self.assertLess(interval, tail)

    def test_chi_square_f_and_exponential_relationships(self):
        expected = 1 - math.exp(-1)
        self.assertAlmostEqual(self.value('Qui-quadrado', {'df': 2}, 'cdf', 2), expected)
        self.assertAlmostEqual(self.value('Exponencial', {'scale': 2}, 'cdf', 2), expected)
        self.assertAlmostEqual(self.value('Exponencial', {'scale': 2}, 'quantile', .5), 2 * math.log(2))
        self.assertAlmostEqual(self.value('F', {'df1': 1, 'df2': 1}, 'cdf', 1), .5)
        self.assertAlmostEqual(self.value('F', {'df1': 1, 'df2': 1}, 'density', 1), 1 / (2 * math.pi))

    def test_binomial_inclusive_intervals_and_fractional_limits(self):
        params = dict(n=5, p=.5)
        self.assertAlmostEqual(self.value('Binomial', params, 'density', 2), 10 / 32)
        self.assertAlmostEqual(self.value('Binomial', params, 'cdf', 2), .5)
        self.assertAlmostEqual(self.value('Binomial', params, 'sf', 2), .5)
        self.assertAlmostEqual(self.value('Binomial', params, 'interval', 2, 3), 20 / 32)
        self.assertAlmostEqual(self.value('Binomial', params, 'interval', 2, 2), 10 / 32)
        self.assertEqual(self.value('Binomial', params, 'interval', 2.1, 2.9), 0)
        self.assertEqual(self.value('Binomial', params, 'density', 2.5), 0)
        self.assertEqual(self.value('Binomial', dict(n=0, p=.5), 'density', 0), 1)

    def test_poisson_analytical_and_degenerate_values(self):
        self.assertAlmostEqual(self.value('Poisson', {'mean': 2}, 'density', 0), math.exp(-2))
        self.assertAlmostEqual(self.value('Poisson', {'mean': 2}, 'interval', 1, 2), 4 * math.exp(-2))
        self.assertAlmostEqual(self.value('Poisson', {'mean': 2}, 'sf', 1), 1 - 3 * math.exp(-2))
        self.assertEqual(self.value('Poisson', {'mean': 0}, 'cdf', 0), 1)

    def test_uniform_weibull_lognormal_gamma_and_beta_parameterizations(self):
        self.assertEqual(self.value('Uniforme', {'lower': 2, 'upper': 6}, 'density', 4), .25)
        self.assertEqual(self.value('Uniforme', {'lower': 2, 'upper': 6}, 'interval', 3, 5), .5)
        self.assertAlmostEqual(self.value('Weibull', {'shape': 1, 'scale': 2}, 'cdf', 2), 1 - math.exp(-1))
        self.assertAlmostEqual(self.value('Gama', {'shape': 1, 'scale': 2}, 'cdf', 2), 1 - math.exp(-1))
        self.assertAlmostEqual(self.value('Lognormal', {'meanlog': 2, 'sdlog': 1}, 'quantile', .5), math.exp(2))
        self.assertAlmostEqual(self.value('Beta', {'alpha': 2, 'beta': 2}, 'density', .5), 1.5)
        self.assertAlmostEqual(self.value('Beta', {'alpha': 1, 'beta': 1}, 'cdf', .25), .25)
        self.assertEqual(self.value('Beta', {'alpha': .5, 'beta': .5}, 'density', 0), math.inf)

    def test_quantile_roundtrip_and_discrete_inequalities_for_all_families(self):
        for name, fields in DISTRIBUTIONS.items():
            params = {key: default for key, _, default in fields}
            dist, discrete, _ = frozen_distribution(name, params)
            for p in (.1, .5, .9):
                with self.subTest(name=name, p=p):
                    x = self.value(name, params, 'quantile', p)
                    upper = self.value(name, params, 'isf', p)
                    if discrete:
                        self.assertGreaterEqual(float(dist.cdf(x)) + 1e-13, p)
                        self.assertLess(float(dist.cdf(x - 1)), p)
                        self.assertLessEqual(float(dist.sf(upper)), p + 1e-13)
                    else:
                        self.assertAlmostEqual(float(dist.cdf(x)), p, places=11)
                        self.assertAlmostEqual(float(dist.sf(upper)), p, places=11)

    def test_invalid_parameters_and_inputs_are_rejected(self):
        cases = [('Normal', dict(mean=0, sd=0)), ('Poisson', dict(mean=-1)),
                 ('Binomial', dict(n=1.5, p=.5)), ('Binomial', dict(n=5, p=2)),
                 ('Uniforme', dict(lower=2, upper=1)), ('t de Student', dict(df=0)),
                 ('Gama', dict(shape=1, scale=-1)), ('Lognormal', dict(meanlog=1000, sdlog=1)),
                 ('Normal', dict(mean=math.inf, sd=1)), ('Normal', dict(mean=0))]
        for name, params in cases:
            with self.subTest(name=name, params=params), self.assertRaises(ValueError):
                self.value(name, params, 'cdf', 0)
        for op, x, upper in [('quantile', 0, None), ('isf', 1, None), ('interval', 2, 1), ('cdf', math.nan, None), ('bad', 0, None)]:
            with self.assertRaises(ValueError):
                self.value('Normal', dict(mean=0, sd=1), op, x, upper)

    def test_report_distinguishes_density_from_point_probability(self):
        normal = distribution_calculation('Normal', dict(mean=0, sd=1), 'density', 0)
        self.assertIn('é densidade', format_distribution(normal))
        binomial = distribution_calculation('Binomial', dict(n=5, p=.5), 'density', 2)
        self.assertIn('P(X=2)', format_distribution(binomial))


if __name__ == '__main__':
    unittest.main()
