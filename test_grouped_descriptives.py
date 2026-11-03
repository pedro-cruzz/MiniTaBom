import unittest
from core import grouped_describe, descriptive_report


class GroupedDescriptiveTests(unittest.TestCase):
    def test_multiple_responses_use_independent_missing_counts(self):
        headers = ['X', 'Y', 'Grupo']
        rows = [['1', '10', 'A'], ['3', '*', 'A'], ['5', '30', 'B'],
                ['*', '40', 'B'], ['7', '50', '*'], ['9', '60', 'A']]
        records, excluded = grouped_describe(headers, rows, [0, 1], [2])
        values = {(r['column'], r['levels']): r['statistics'] for r in records}
        self.assertEqual(excluded, 1)
        self.assertEqual(values[0, ('A',)]['Soma'], 13)
        self.assertEqual(values[0, ('A',)]['N'], 3)
        self.assertEqual(values[1, ('A',)]['Média'], 35)
        self.assertEqual(values[1, ('A',)]['Ausentes'], 1)
        self.assertEqual(values[0, ('B',)]['N total'], 2)
        self.assertIsNone(values[0, ('B',)]['Variância amostral'])

    def test_combination_grid_and_all_missing_response_have_zero_n(self):
        records, _ = grouped_describe(['X', 'Grupo', 'Turno'],
            [['*', 'A', 'Dia'], ['', 'A', 'Dia'], ['8', 'B', 'Noite']], [0], [1, 2], include_empty=True)
        self.assertEqual([r['levels'] for r in records],
                         [('A', 'Dia'), ('A', 'Noite'), ('B', 'Dia'), ('B', 'Noite')])
        missing, empty = records[0]['statistics'], records[1]['statistics']
        self.assertEqual((missing['N'], missing['Ausentes'], missing['N total']), (0, 2, 2))
        self.assertEqual((empty['N'], empty['Ausentes'], empty['N total']), (0, 0, 0))
        self.assertIsNone(missing['Média'])
        self.assertIsNone(empty['Soma'])

    def test_missing_group_is_distinct_from_literal_label(self):
        records, excluded = grouped_describe(['X', 'Grupo'],
            [['1', ''], ['3', '*'], ['9', '[ausente]']], [0], [1], include_missing=True)
        self.assertEqual(excluded, 0)
        self.assertEqual([r['levels'] for r in records], [(None,), ('[ausente]',)])
        self.assertEqual(records[0]['statistics']['Média'], 2)
        self.assertEqual(records[1]['statistics']['Média'], 9)

    def test_grouping_preserves_first_appearance_and_sequence(self):
        records, _ = grouped_describe(['X', 'G'],
            [['1', ' B '], ['100', 'A'], ['4', 'B'], ['*', 'B'], ['2', 'B']], [0], [1])
        self.assertEqual([r['levels'] for r in records], [('B',), ('A',)])
        self.assertEqual(records[0]['statistics']['MSSD'], 13 / 4)

    def test_invalid_response_reports_original_row_and_excluded_rows_are_ignored(self):
        rows = [['texto excluído', '*'], ['1', 'A'], ['inválido', 'B']]
        with self.assertRaisesRegex(ValueError, 'X: Linha 4'):
            grouped_describe(['X', 'G'], rows, [0], [1])
        for invalid in ['nan', 'inf']:
            with self.assertRaisesRegex(ValueError, 'Linha 3'):
                grouped_describe(['X', 'G'], [['1', 'A'], [invalid, 'B']], [0], [1])

    def test_invalid_selections_and_empty_group_set(self):
        for columns, by in [([], [1]), ([0], []), ([0], [0]), ([0], [1, 1]),
                            ([0, 0], [1]), ([0], [True]), ([0], [9])]:
            with self.subTest(columns=columns, by=by), self.assertRaises(ValueError):
                grouped_describe(['X', 'G'], [['1', 'A']], columns, by)
        with self.assertRaisesRegex(ValueError, 'Nenhum grupo'):
            grouped_describe(['X', 'G'], [['1', '*']], [0], [1])

    def test_cartesian_product_limit_is_checked_before_creating_empty_groups(self):
        rows = [[str(i), str(i), 'A'] for i in range(101)]
        rows += [[str(i), '0', str(i)] for i in range(101)]
        with self.assertRaisesRegex(ValueError, '10.000'):
            grouped_describe(['X', 'G1', 'G2'], rows, [0], [1, 2], include_empty=True)

    def test_report_includes_groups_counts_and_only_requested_statistics(self):
        text = descriptive_report(['X', 'Grupo'], [['1', 'A'], ['3', 'A'], ['5', '*']],
                                  [0], ['N', 'Média'], by=[1], include_missing=True)
        self.assertIn('Estatísticas descritivas: X (por Grupo)', text)
        self.assertIn("Grupo: Grupo = 'A'\nN: 2\nMédia: 2", text)
        self.assertIn('Grupo: Grupo = [ausente]\nN: 1\nMédia: 5', text)
        self.assertNotIn('Variância', text)


if __name__ == '__main__':
    unittest.main()
