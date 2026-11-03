from copy import deepcopy
import unittest
from unittest.mock import patch

from data_operations import sort_rows, stack_columns, unstack_column


class DataOperationTests(unittest.TestCase):
    def test_numeric_sort_is_exact_stable_and_keeps_whole_rows(self):
        headers = ['Valor', 'Identificador']
        rows = [['9007199254740993', 'a'], ['9007199254740992', 'b'], ['2,5', 'c'], ['2.50', 'd']]
        original = deepcopy(rows)
        h, result, meta = sort_rows(headers, rows, [0], types=['numeric'])
        self.assertEqual([r[1] for r in result], ['c', 'd', 'b', 'a'])
        self.assertEqual(rows, original)
        result[0][0] = 'mutado'
        self.assertEqual(rows, original)
        self.assertTrue(meta['changed'])
        self.assertEqual(h, headers)

    def test_multiple_keys_directions_and_missing_position(self):
        rows = [['B', '2', 'a'], ['A', '1', 'b'], ['A', '3', 'c'], ['A', '*', 'd'], ['B', '', 'e'], ['A', '3', 'f']]
        _, r, _ = sort_rows(['G', 'X', 'ID'], rows, [0, 1], types=['text', 'numeric'], descending=[False, True])
        self.assertEqual([v[2] for v in r], ['c', 'f', 'b', 'd', 'a', 'e'])
        _, r, _ = sort_rows(['G', 'X', 'ID'], rows, [1], descending=[True], missing_last=False)
        self.assertEqual([v[2] for v in r], ['d', 'e', 'c', 'f', 'a', 'b'])

    def test_automatic_types_and_text_case_policy(self):
        _, r, meta = sort_rows(['X'], [['10'], ['2']], [0])
        self.assertEqual(r, [['2'], ['10']])
        self.assertIn('numérico', meta['details'][0])
        _, r, meta = sort_rows(['X'], [['b'], ['A'], ['a']], [0], case_sensitive=False)
        self.assertEqual(r, [['A'], ['a'], ['b']])
        self.assertIn('texto', meta['details'][0])
        _, _, meta = sort_rows(['X'], [['1'], ['2']], [0])
        self.assertFalse(meta['changed'])

    def test_sort_errors_do_not_partially_mutate_inputs(self):
        rows = [['2', 'b'], ['1', 'a'], ['bad', 'c']]
        original = deepcopy(rows)
        with self.assertRaisesRegex(ValueError, 'Linha 3'):
            sort_rows(['X', 'G'], rows, [0], types=['numeric'])
        self.assertEqual(rows, original)
        for keys in ([], [0, 0], [-1], [True]):
            with self.subTest(keys=keys), self.assertRaises(ValueError):
                sort_rows(['X', 'G'], rows, keys)

    def test_stack_preserves_sources_literals_and_specified_column_order(self):
        rows = [['1,5', 'a'], ['*', 'b']]
        original = deepcopy(rows)
        headers, result, meta = stack_columns(['A', 'B'], rows, [1, 0])
        self.assertEqual(headers, ['A', 'B', 'Valor', 'Origem'])
        self.assertEqual([r[2:] for r in result], [['a', 'B'], ['b', 'B'], ['1,5', 'A'], ['*', 'A']])
        self.assertEqual([r[:2] for r in result], original + [['', ''], ['', '']])
        self.assertEqual(rows, original)
        self.assertEqual(meta['rows'], 4)

    def test_stack_omission_empty_input_and_destination_validation(self):
        h, r, m = stack_columns(['A', 'B'], [['1', ''], ['*', '2']], [0, 1], omit_missing=True)
        self.assertEqual([row[2:] for row in r], [['1', 'A'], ['2', 'B']])
        self.assertEqual(m['omitted'], 2)
        for options in [dict(value_name='A'), dict(value_name=''), dict(value_name='Mesmo', label_name='Mesmo')]:
            with self.subTest(options=options), self.assertRaises(ValueError):
                stack_columns(['A', 'B'], [['1', '2']], [0, 1], **options)
        with self.assertRaises(ValueError):
            stack_columns(['A'], [['*']], [0], omit_missing=True)

    def test_unstack_order_missing_groups_and_name_collisions(self):
        headers = ['V', 'G', "Separado ['B']"]
        rows = [['1', ' B ', 'x'], ['2', 'A', 'x'], ['*', 'B', 'x'], ['4', '*', 'x'], ['5', 'ausente', 'x']]
        h, r, meta = unstack_column(headers, rows, 0, 1, include_missing_groups=True)
        self.assertEqual(h[3:], ["Separado ['B'] (2)", "Separado ['A']", 'Separado [ausente]', "Separado ['ausente']"])
        self.assertEqual(r[0][3:], ['1', '2', '4', '5'])
        self.assertEqual(r[1][3:], ['*', '', '', ''])
        self.assertEqual([v[:3] for v in r], rows)
        self.assertEqual(meta['missing_groups'], 0)

    def test_stack_unstack_round_trip_preserves_missing_and_decimal_text(self):
        original = [['1,25', 'b'], ['', 'c'], ['*', 'd']]
        h, rows, _ = stack_columns(['A', 'B'], original, [0, 1])
        h, rows, _ = unstack_column(h, rows, 2, 3)
        self.assertEqual([r[-2:] for r in rows[:3]], original)

    def test_unstack_omits_only_selected_missing_values_and_retains_empty_group_column(self):
        h, r, meta = unstack_column(['V', 'G'], [['1', 'B'], ['*', 'A'], ['2', '*']], 0, 1, omit_missing=True)
        self.assertEqual(h[2:], ["Separado ['B']", "Separado ['A']"])
        self.assertEqual([row[2:] for row in r], [['1', ''], ['', ''], ['', '']])
        self.assertEqual((meta['omitted'], meta['missing_groups']), (1, 1))

    def test_invalid_shapes_and_output_limits_fail_before_mutation(self):
        rows = [['1', 'A'], ['2', 'B']]
        original = deepcopy(rows)
        with patch('data_operations.MAX_CELLS', 5), self.assertRaises(ValueError):
            stack_columns(['V', 'G'], rows, [0, 1])
        with patch('data_operations.MAX_COLUMNS', 3), self.assertRaises(ValueError):
            unstack_column(['V', 'G'], rows, 0, 1)
        self.assertEqual(rows, original)
        with self.assertRaises(ValueError):
            sort_rows(['V', 'G'], [['1']], [0])
        with self.assertRaises(ValueError):
            unstack_column(['V', 'G'], rows, 0, 0)


if __name__ == '__main__':
    unittest.main()
