"""Integração dos novos diálogos em Tk oculto; sem interação com o desktop."""
import unittest
from unittest.mock import patch

from app import MiniTaBom


def replace(entry, value):
    entry.delete(0, 'end')
    entry.insert(0, str(value))


class ExtendedInterfaceTests(unittest.TestCase):
    def setUp(self):
        self.app = MiniTaBom()
        self.addCleanup(self.app.destroy)
        self.app.withdraw()
        self.app.update_idletasks()

    def test_two_proportion_summary_dialog_report_and_navigation(self):
        d = self.app.extended_test_dialog('two_proportions')
        self.assertTrue(d.tabs.tab(0, 'image'))
        d.source.current(2)
        d.toggle_source()
        for entry, value in zip(d.ns + d.values, [100, 100, 30, 20]):
            replace(entry, value)
        d.pooled.set(True)
        d.submit()
        self.assertFalse(d.winfo_exists())
        output = self.app.output.get('1.0', 'end')
        self.assertIn('TESTE DE DUAS PROPORÇÕES', output)
        self.assertIn('Fisher exato', output)
        self.assertIn('combinada sob H0', output)
        self.assertEqual(len(self.app.navigator.get_children('results')), 1)
        self.assertTrue(self.app.dirty)

    def test_variance_raw_summary_measure_and_ci_only(self):
        d = self.app.extended_test_dialog('one_variance')
        d.submit()
        self.assertFalse(d.winfo_exists())
        d = self.app.extended_test_dialog('two_variances')
        d.source.current(2)
        d.toggle_source()
        d.measure.current(1)
        d.update_measure()
        self.assertIn('Variância', d.value_labels[0].cget('text'))
        for entry, value in zip(d.ns + d.values, [3, 3, 8, 2]):
            replace(entry, value)
        d.perform_test.set(False)
        d.toggle_test()
        self.assertTrue(d.null.instate(['disabled']))
        d.submit()
        self.assertFalse(d.winfo_exists())
        output = self.app.output.get('1.0', 'end').split('TESTE DE DUAS VARIÂNCIAS')[1]
        self.assertIn('σ1² / σ2²', output)
        self.assertNotIn('Valor-p', output)
        self.assertNotIn('H0:', output)
        self.assertEqual(len(self.app.navigator.get_children('results')), 2)

    def test_stacked_proportions_and_errors_leave_session_unchanged(self):
        self.app.headers = ['Resultado', 'Grupo']
        self.app.rows = [['Sim', 'B'], ['Não', 'A'], ['Não', 'B'], ['Sim', 'A']]
        self.app.refresh()
        d = self.app.extended_test_dialog('two_proportions')
        d.source.current(1)
        d.toggle_source()
        d.submit()
        self.assertFalse(d.winfo_exists())
        self.assertIn("grupo 'B'", self.app.output.get('1.0', 'end'))
        d = self.app.extended_test_dialog('two_variances')
        before = self.app.output.get('1.0', 'end')
        with patch('app.messagebox.showerror') as error:
            d.submit()
        error.assert_called_once()
        self.assertTrue(d.winfo_exists())

        self.assertEqual(before, self.app.output.get('1.0', 'end'))
        d.destroy()
        d = self.app.extended_test_dialog('one_variance')
        d.source.current(1)
        replace(d.ns[0], '1,5')
        replace(d.values[0], '2')
        with patch('extended_inference_dialog.messagebox.showerror') as error:
            d.submit()
        error.assert_called_once()
        self.assertTrue(d.winfo_exists())

    def test_contingency_raw_weighted_dialog_and_result_index(self):
        self.app.headers = ['Grupo', 'Resultado', 'N']
        self.app.rows = [['A', 'Sim', '30'], ['A', 'Não', '10'], ['B', 'Sim', '10'], ['B', 'Não', '30']]
        self.app.refresh()
        d = self.app.contingency_dialog()
        self.assertTrue(d.tabs.tab(0, 'image'))
        d.count_column.current(3)
        d.show_percentages.set(True)
        d.show_residuals.set(True)
        d.submit()
        self.assertFalse(d.winfo_exists())
        output = self.app.output.get('1.0', 'end')
        self.assertIn('Pearson = 20', output)
        self.assertIn('Resíduos ajustados:', output)
        self.assertIn('% da linha:', output)
        self.assertEqual(len(self.app.navigator.get_children('results')), 1)

    def test_contingency_matrix_error_is_atomic_and_dialog_can_be_corrected(self):
        self.app.headers = ['Sim', 'Não', 'Grupo']
        self.app.rows = [['30', '10', 'A'], ['10', '30', 'B']]
        self.app.refresh()
        d = self.app.contingency_dialog()
        d.source.current(1)
        d.toggle_source()
        before = self.app.output.get('1.0', 'end')
        with patch('app.messagebox.showerror') as error:
            d.submit()
        error.assert_called_once()
        self.assertTrue(d.winfo_exists())
        self.assertEqual(self.app.output.get('1.0', 'end'), before)
        d.columns.selection_set(0, 1)
        d.label_column.current(3)
        d.submit()
        self.assertFalse(d.winfo_exists())
        self.assertIn('Pearson = 20', self.app.output.get('1.0', 'end'))

    def test_normality_dialog_success_and_constant_data_error(self):
        d = self.app.normality_dialog()
        self.assertTrue(d.tabs.tab(0, 'image'))
        d.submit()
        self.assertFalse(d.winfo_exists())
        self.assertIn('TESTE DE NORMALIDADE', self.app.output.get('1.0', 'end'))
        self.assertEqual(len(self.app.navigator.get_children('results')), 1)
        self.app.rows = [['1', 'A']] * 5
        self.app.refresh()
        d = self.app.normality_dialog()
        before = self.app.output.get('1.0', 'end')
        with patch('app.messagebox.showerror') as error:
            d.submit()
        error.assert_called_once()
        self.assertTrue(d.winfo_exists())
        self.assertEqual(self.app.output.get('1.0', 'end'), before)


if __name__ == '__main__':
    unittest.main()
