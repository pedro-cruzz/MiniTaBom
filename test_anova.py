import math
import unittest
from anova import prepare_groups, one_way, format_anova_report
from inference import two_sample, scientific_stats


def groups(*samples):
    return [dict(label=f'Grupo {i + 1}', values=list(sample)) for i, sample in enumerate(samples)]


class AnovaTests(unittest.TestCase):
    def test_analytical_balanced_table(self):
        result = one_way(groups([1, 2, 3], [4, 5, 6], [7, 8, 9]))
        self.assertEqual(result['overall'], 5)
        self.assertEqual(result['n'], 9)
        self.assertEqual(result['ss_between'], 54)
        self.assertEqual(result['ss_within'], 6)
        self.assertEqual(result['ss_total'], 60)
        self.assertEqual((result['df1'], result['df2']), (2, 6))
        self.assertEqual(result['f'], 27)
        # Sobrevivência de F(2,6): (1 + F/3)^(-3).
        self.assertAlmostEqual(result['p'], .001, places=13)
        self.assertEqual(result['s'], 1)
        self.assertEqual(result['r_squared'], 90)
        self.assertIn('IC individual', format_anova_report(result))

    def test_two_groups_agree_with_t_squared(self):
        first, second = [2, 4, 5, 9, 15], [1, 2, 4, 6, 7, 8]
        for equal_var in (True, False):
            with self.subTest(equal_var=equal_var):
                result = one_way(groups(first, second), equal_var=equal_var)
                t = two_sample(first, second, equal_var=equal_var, legacy_df=False)
                self.assertAlmostEqual(result['f'], t['t'] ** 2, places=12)
                self.assertAlmostEqual(result['p'], t['p'], places=12)
                self.assertAlmostEqual(result['df2'], t['df'], places=12)

    def test_unbalanced_welch_and_classical_match_scipy_anova_api(self):
        data = [[1, 2, 3, 5], [3, 8, 10], [7, 8, 10, 20, 25]]
        stats = scientific_stats()
        for equal_var in (True, False):
            result = one_way(groups(*data), equal_var=equal_var)
            reference = stats.f_oneway(*data, equal_var=equal_var)
            self.assertAlmostEqual(result['f'], reference.statistic, places=12)
            self.assertAlmostEqual(result['p'], reference.pvalue, places=12)

    def test_group_formats_agree_with_missing_and_first_appearance_order(self):
        stacked, excluded = prepare_groups(['Medição', 'Grupo'],
            [['1', 'B'], ['2', 'B'], ['4', 'A'], ['5', 'A'], ['*', 'A'], ['9', ''] ],
            response=0, factor=1)
        separate, _ = prepare_groups(['B', 'A'], [['1', '4'], ['2', '5']], columns=[0, 1])
        self.assertEqual([g['label'] for g in stacked], ['B', 'A'])
        self.assertEqual(excluded, 2)
        self.assertAlmostEqual(one_way(stacked)['f'], one_way(separate)['f'])

    def test_translation_scale_and_group_order_invariance(self):
        data = [[1, 2, 3], [4, 6, 8], [10, 11, 14]]
        for equal_var in (True, False):
            baseline = one_way(groups(*data), equal_var=equal_var)
            transformed = one_way(groups(*[[7 * v + 100 for v in sample] for sample in reversed(data)]), equal_var=equal_var)
            self.assertAlmostEqual(baseline['f'], transformed['f'], places=10)
            self.assertAlmostEqual(baseline['p'], transformed['p'], places=12)

    def test_pairwise_methods_adjusted_ci_and_sign(self):
        data = groups([1, 2, 3, 4], [10, 11, 12, 13], [15, 17, 19, 21])
        for equal_var, method in [(True, 'Tukey-Kramer'), (False, 'Games-Howell')]:
            result = one_way(data, equal_var=equal_var, comparisons=True)
            self.assertEqual(result['comparison_method'], method)
            self.assertEqual(len(result['comparisons']), 3)
            first_pair = result['comparisons'][0]
            self.assertEqual(first_pair['difference'], -9)
            self.assertLess(first_pair['high'], 0)
            self.assertLess(first_pair['p'], .05)
            self.assertIn(method, format_anova_report(result))

    def test_invalid_and_zero_variance_contracts(self):
        for data in (groups([1], [2, 3]), groups([1, 1], [2, 2]), groups([1, 2]),
                     groups([math.nan, 1], [2, 3]), groups([-1e308, 1e308], [2, 3])):
            with self.assertRaises(ValueError):
                one_way(data)
        with self.assertRaisesRegex(ValueError, 'Welch exige'):
            one_way(groups([1, 1], [2, 3]), equal_var=False)
        with self.assertRaises(ValueError):
            one_way(groups([1, 2], [3, 4]), confidence=100)
        for selection in (dict(columns=[0]), dict(columns=[0, 0]), dict(response=0, factor=0)):
            with self.assertRaises(ValueError):
                prepare_groups(['A', 'B'], [['1', '2']], **selection)


if __name__ == '__main__':
    unittest.main()
