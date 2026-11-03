import math, unittest
from core import describe, histogram, numeric_column, read_table, descriptive_report

class CoreTests(unittest.TestCase):
    def test_trimmed_mean_rounding_boundaries(self):
        for n, trim in [(9, 0), (10, 1), (11, 1), (29, 1), (30, 2)]:
            values = list(range(n - 1)) + [1000]
            expected = sum(sorted(values)[trim:n-trim]) / (n - 2 * trim)
            self.assertEqual(describe(values)['Média aparada (5% por ponta)'], expected)

    def test_mode_ties_constants_and_no_repetition(self):
        self.assertEqual(describe([3, 1, 3, 1, 9])['Moda'], (1, 3))
        self.assertEqual(describe([3, 1, 3, 1, 9])['Frequência da moda'], 2)
        self.assertEqual(describe([4, 4, 4])['Moda'], (4,))
        self.assertIsNone(describe([1, 2, 3])['Moda'])
        self.assertIsNone(describe([1])['Frequência da moda'])

    def test_adjusted_moments_analytical_and_small_samples(self):
        self.assertAlmostEqual(describe([0, 0, 1])['Assimetria'], math.sqrt(3))
        self.assertAlmostEqual(describe([1, 2, 3, 4])['Assimetria'], 0)
        self.assertAlmostEqual(describe([1, 2, 3, 4])['Curtose (excesso)'], -1.2)
        for values in [[1], [1, 2], [4, 4, 4, 4]]:
            self.assertIsNone(describe(values)['Assimetria'])
        self.assertIsNone(describe([1, 2, 3])['Curtose (excesso)'])
        self.assertIsNone(describe([4] * 4)['Curtose (excesso)'])

    def test_moments_invariance_and_mssd_order(self):
        values = [1, 2, 4, 8, 10]
        original = describe(values)
        transformed = describe([100 - 3 * v for v in values])
        self.assertAlmostEqual(transformed['Assimetria'], -original['Assimetria'])
        self.assertAlmostEqual(transformed['Curtose (excesso)'], original['Curtose (excesso)'])
        self.assertAlmostEqual(transformed['MSSD'], 9 * original['MSSD'])
        self.assertEqual(describe([1, 4, 2])['MSSD'], 13 / 4)
        self.assertEqual(describe([1, 2, 4])['MSSD'], 5 / 4)
        self.assertIsNone(describe([1])['MSSD'])
        self.assertEqual(describe([4, 4, 4])['MSSD'], 0)

    def test_extended_report_modes_and_missing_sequence_contract(self):
        report = descriptive_report(['A'], [['1'], ['*'], ['4'], ['2']], [0], ['MSSD', 'Ausentes'])
        self.assertIn('MSSD: 3.25', report)
        self.assertIn('Ausentes: 1', report)
        report = descriptive_report(['A'], [['2'], ['1'], ['2'], ['1']], [0], ['Moda', 'Frequência da moda'])
        self.assertIn('Moda: 1; 2\nFrequência da moda: 2', report)

    def test_quartiles_interpolate_documented_positions(self):
        result = describe(list(range(10, 0, -1)), 2)
        self.assertEqual(result['Q1'], 2.75)
        self.assertEqual(result['Q3'], 8.25)
        self.assertEqual(result['Intervalo interquartil'], 5.5)
        self.assertEqual(result['Amplitude'], 9)
        self.assertEqual(result['Soma dos quadrados'], 385)
        self.assertEqual(result['N total'], 12)

    def test_small_sample_convention_and_constant_data(self):
        singleton = describe([7])
        self.assertEqual((singleton['Q1'], singleton['Q3']), (7, 7))
        self.assertIsNone(singleton['Coeficiente de variação (%)'])
        pair = describe([1, 9])
        self.assertEqual((pair['Q1'], pair['Q3']), (1, 9))
        self.assertEqual(describe([4, 4, 4])['Coeficiente de variação (%)'], 0)
        self.assertIsNone(describe([-1, 1])['Coeficiente de variação (%)'])
        self.assertAlmostEqual(describe([-1, -3])['Coeficiente de variação (%)'], -50 * math.sqrt(2))

    def test_extended_statistics_translation_and_scale(self):
        original = describe([1, 2, 4, 8, 10])
        shifted = describe([101, 102, 104, 108, 110])
        scaled = describe([3, 6, 12, 24, 30])
        for key in ['Amplitude', 'Intervalo interquartil', 'Desvio padrão amostral']:
            self.assertAlmostEqual(shifted[key], original[key])
            self.assertAlmostEqual(scaled[key], 3 * original[key])
        self.assertAlmostEqual(scaled['Soma dos quadrados'], 9 * original['Soma dos quadrados'])

    def test_overflow_becomes_useful_error(self):
        with self.assertRaisesRegex(ValueError, 'Magnitude'):
            describe([1e308, -1e308])
        for missing in [-1, 0.5, True]:
            with self.assertRaises(ValueError):
                describe([1], missing)

    def test_report_multiple_columns_and_missing(self):
        report = descriptive_report(['Antes', 'Depois'], [['1,5', '4'], ['*', '6']],
                                    [0, 1], ['N', 'Ausentes', 'Média'])
        self.assertIn('Antes\nN: 1\nAusentes: 1\nMédia: 1.5', report)
        self.assertIn('Depois\nN: 2\nAusentes: 0\nMédia: 5', report)
        self.assertNotIn('Q1', report)
        with self.assertRaisesRegex(ValueError, 'Depois: Linha 2'):
            descriptive_report(['Antes', 'Depois'], [['1', 'abc']], [0, 1], ['Média'])
        for columns, selected in [([], ['N']), ([0], []), ([2], ['N']), ([0], ['inventado'])]:
            with self.assertRaises(ValueError):
                descriptive_report(['A'], [['1']], columns, selected)

    def test_known_sample(self):
        r = describe([2,4,4,4,5,5,7,9])
        self.assertEqual(r['Média'],5)
        self.assertEqual(r['Mediana'],4.5)
        self.assertAlmostEqual(r['Variância amostral'],32/7)
        self.assertAlmostEqual(r['Erro padrão'],math.sqrt(4/7))

    def test_empty_singleton(self):
        self.assertIsNone(describe([3])['Desvio padrão amostral'])
        with self.assertRaises(ValueError):
            describe([])

    def test_csv_missing_decimal(self):
        headers, rows = read_table('Valor;Grupo\n1,5;A\n*;B\n;C\n2,5;D\n')
        self.assertEqual(headers,['Valor','Grupo'])
        self.assertEqual(numeric_column(rows,0),([1.5,2.5],2))

    def test_invalid(self):
        for v in ['abc','nan','inf']:
            with self.assertRaises(ValueError):
                numeric_column([[v]],0)
        with self.assertRaises(ValueError):
            read_table('A;B\n1;2;3\n')
        with self.assertRaises(ValueError):
            read_table('A;A\n1;2\n')

    def test_histogram(self):
        edges, counts = histogram([0,1,2,3,4,5])
        self.assertEqual(sum(counts),6)
        self.assertEqual((edges[0],edges[-1]),(0,5))
        self.assertEqual(histogram([7,7])[1],[2])

if __name__ == '__main__':
    unittest.main()
