import unittest
from history import WorksheetHistory
from core import boxplot


class HistoryTests(unittest.TestCase):
    def test_undo_redo_and_branch(self):
        headers, rows = ['A'], [['1']]
        history = WorksheetHistory(headers, rows)
        rows[0][0] = '2'
        history.record(headers, rows)
        self.assertEqual(history.undo(), (['A'], [['1']]))
        self.assertEqual(history.redo(), (['A'], [['2']]))
        history.undo()
        history.record(headers, [['3']])
        self.assertIsNone(history.redo())
        self.assertEqual(history.undo(), (['A'], [['1']]))

    def test_history_does_not_alias_data_and_limits_snapshots(self):
        history = WorksheetHistory(['A'], [['0']], limit=2)
        for value in ('1', '2', '3'):
            history.record(['A'], [[value]])
        restored = history.undo()
        restored[1][0][0] = 'alterado fora do histórico'
        self.assertEqual(history.redo()[1], [['3']])
        self.assertEqual(history.undo()[1], [['2']])
        self.assertEqual(history.undo()[1], [['1']])
        self.assertIsNone(history.undo())


class BoxplotTests(unittest.TestCase):
    def test_documented_example_and_ingrown_whisker(self):
        result = boxplot([1200, 1443, 1490, 1528, 1563, 2479])
        self.assertEqual(result['q1'], 1382.25)
        self.assertEqual(result['q3'], 1792)
        self.assertEqual(result['median'], 1509)
        self.assertEqual((result['low'], result['high']), (1200, 1563))
        self.assertEqual(result['outliers'], [2479])

    def test_constant_singleton_and_zero_iqr(self):
        self.assertEqual(boxplot([3])['median'], 3)
        self.assertEqual(boxplot([4, 4, 4])['outliers'], [])
        result = boxplot([0] * 9 + [100])
        self.assertEqual(result['outliers'], [100])
        self.assertEqual((result['low'], result['high']), (0, 0))

    def test_invalid_and_extreme_input(self):
        for values in ([], [float('nan')], [float('inf')], [-1e308, 1e308]):
            with self.assertRaises(ValueError):
                boxplot(values)


if __name__ == '__main__':
    unittest.main()
