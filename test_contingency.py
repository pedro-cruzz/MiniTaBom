import math
import unittest
from copy import deepcopy

from contingency import chi_square_table, categorical_table, matrix_table, format_contingency, MAX_TOTAL


class ContingencyTests(unittest.TestCase):
    def test_2x2_closed_case_no_yates_and_independent_fisher(self):
        r = chi_square_table([[30, 10], [10, 30]], ['A', 'B'], ['Sim', 'Não'])
        self.assertEqual((r['pearson'], r['df'], r['total']), (20, 1, 80))
        self.assertAlmostEqual(r['p'], math.erfc(math.sqrt(10)), places=14)
        self.assertEqual(r['expected'], [[20, 20], [20, 20]])
        self.assertEqual(r['contributions'], [[5, 5], [5, 5]])
        self.assertEqual(r['adjusted'][0][0], 10 / math.sqrt(5))
        self.assertAlmostEqual(r['likelihood'], 2 * (60 * math.log(1.5) + 20 * math.log(.5)))
        denominator = math.comb(80, 40)
        probabilities = [math.comb(40, x) * math.comb(40, 40 - x) / denominator for x in range(41)]
        exact = sum(p for p in probabilities if p <= probabilities[30] * (1 + 1e-12))
        self.assertAlmostEqual(r['fisher'], exact, places=14)

    def test_2x3_analytic_df2_and_margins(self):
        r = chi_square_table([[10, 20, 30], [20, 30, 40]])
        self.assertEqual(r['expected'], [[12, 20, 28], [18, 30, 42]])
        expected_statistic = 4/12 + 4/28 + 4/18 + 4/42
        self.assertAlmostEqual(r['pearson'], expected_statistic)
        self.assertAlmostEqual(r['p'], math.exp(-expected_statistic / 2))
        self.assertEqual((r['row_totals'], r['column_totals']), ([60, 90], [30, 50, 70]))
        self.assertIsNone(r['fisher'])
        for expected, total in zip(r['expected'], r['row_totals']):
            self.assertAlmostEqual(sum(expected), total)

    def test_zero_observed_cells_and_small_expected_suppression(self):
        r = chi_square_table([[0, 10], [10, 0]])
        self.assertAlmostEqual(r['likelihood'], 40 * math.log(2))
        self.assertEqual(r['pearson'], 20)
        self.assertTrue(math.isfinite(r['likelihood_p']))
        small = chi_square_table([[1, 0], [0, 1]])
        self.assertEqual((small['below_one'], small['below_five']), (4, 4))
        self.assertIsNone(small['p'])
        self.assertIsNone(small['likelihood_p'])
        self.assertEqual(small['fisher'], 1)
        text = format_contingency(small)
        self.assertIn('valores-p assintóticos não são exibidos', text)
        self.assertIn('não exibido', text)

    def test_nearly_independent_large_table_is_stable_and_exact_bounded(self):
        n = 10**12
        r = chi_square_table([[n + 1, n - 1], [n - 1, n + 1]])
        self.assertAlmostEqual(r['pearson'], 4 / n, places=24)
        self.assertAlmostEqual(r['likelihood'], 4 / n, places=24)
        self.assertGreaterEqual(r['likelihood_p'], 0)
        self.assertIsNone(r['fisher'])
        self.assertTrue(r['fisher_limited'])
        self.assertIn('limite operacional', format_contingency(r))

    def test_categorical_weighted_equals_expanded_preserves_order_and_data(self):
        weighted = [[' B ', 'Sim', '3'], ['A', 'Não', '4'], ['B', 'Não', '2'], ['A', 'Sim', '1'],
                    ['X', 'Y', '0'], ['', 'Sim', '8'], ['A', 'Sim', '*']]
        original = deepcopy(weighted)
        r = categorical_table(['Grupo', 'Resultado', 'N'], weighted, 0, 1, 2)
        expanded = [[a.strip(), b] for a, b, n in weighted[:4] for _ in range(int(n))]
        e = categorical_table(['Grupo', 'Resultado'], expanded, 0, 1)
        self.assertEqual(r['observed'], [[3, 2], [1, 4]])
        self.assertEqual(r['observed'], e['observed'])
        self.assertEqual(r['row_labels'], ['B', 'A'])
        self.assertEqual((r['missing_rows'], r['zero_rows']), (2, 1))
        self.assertEqual(r['pearson'], e['pearson'])
        self.assertEqual(weighted, original)

    def test_matrix_labels_empty_rows_and_report_options(self):
        rows = [['30', '10', ' B '], ['10', '30', 'A'], ['', '*', '']]
        r = matrix_table(['Sim', 'Não', 'Grupo'], rows, [0, 1], 2)
        self.assertEqual((r['missing_rows'], r['row_labels']), (1, ['B', 'A']))
        plain = format_contingency(r, show_expected=False)
        self.assertNotIn('Esperadas:', plain)
        full = format_contingency(r, show_residuals=True, show_contributions=True, show_percentages=True)
        for label in ('Esperadas:', 'Resíduos brutos:', 'Resíduos padronizados:', 'Resíduos ajustados:',
                      'Contribuições Pearson:', '% da linha:', '% da coluna:', '% do total:'):
            self.assertIn(label, full)

    def test_invalid_tables_and_counts_are_rejected(self):
        for table in ([], [[1, 2]], [[1], [2]], [[1, 2], [3]], [[0, 0], [1, 2]],
                      [[0, 2], [0, 2]], [[-1, 2], [3, 4]], [[1.5, 2], [3, 4]],
                      [[True, 2], [3, 4]], [[MAX_TOTAL, 1], [1, 1]], [[1, 1]] * 51):
            with self.subTest(table=table), self.assertRaises(ValueError):
                chi_square_table(table)
        for labels in (['A'], ['A', 'A'], ['', 'B']):
            with self.assertRaises(ValueError):
                chi_square_table([[1, 2], [3, 4]], row_labels=labels)
        for rows in ([['1', ''], ['3', '4']], [['1,5', '2'], ['3', '4']], [['nan', '2'], ['3', '4']]):
            with self.assertRaises(ValueError):
                matrix_table(['A', 'B'], rows, [0, 1])
        with self.assertRaises(ValueError):
            categorical_table(['A', 'B', 'N'], [['X', 'Y', '-1']], 0, 1, 2)
        with self.assertRaises(ValueError):
            categorical_table(['A', 'B'], [['X', 'Y']], 0, 0)
        with self.assertRaises(ValueError):
            matrix_table(['A', 'B'], [['1', '2'], ['3', '4']], [0, 1], 0)


if __name__ == '__main__':
    unittest.main()
