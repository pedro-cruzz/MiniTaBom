"""Integração Tkinter sem exibir janelas nem alterar o clipboard do usuário."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

from app import MiniTaBom
from project import load_project
from worksheet import paste_block, copy_block, clear_block
from graphs import GraphWindow, GroupGraphWindow
from anova import prepare_groups
from linear_models import linear_regression
from regression_graph import RegressionGraph
from xy_graphs import XYGraphWindow


class PasteTests(unittest.TestCase):
    def test_copy_block_round_trips_quoted_text_and_virtual_rows(self):
        source = [['1,5', 'a\tb'], ['texto\ncom quebra', '"aspas"']]
        text = copy_block(source, (0, 0, 2, 1))
        target = []
        paste_block(target, 2, (0, 0), text)
        self.assertEqual(target, source + [['', '']])
        self.assertEqual(source, [['1,5', 'a\tb'], ['texto\ncom quebra', '"aspas"']])

    def test_clear_block_does_not_materialize_virtual_rows(self):
        rows = [['a', 'b']]
        self.assertFalse(clear_block(rows, (5, 0, 100, 1)))
        self.assertTrue(clear_block(rows, (0, 1, 100, 1)))
        self.assertEqual(rows, [['a', '']])

    def test_paste_preserves_decimals_missing_and_grows_rows(self):
        rows = [['original', 'A', '']]
        self.assertTrue(paste_block(rows, 3, (0, 1), '1,5\t*\r\n2,5\ttexto\r\n'))
        self.assertEqual(rows, [['original', '1,5', '*'], ['', '2,5', 'texto']])

    def test_overwide_later_line_does_not_modify_any_cell(self):
        rows = [['original', 'A']]
        with self.assertRaises(ValueError):
            paste_block(rows, 2, (0, 0), 'válido\n1\t2\t3')
        self.assertEqual(rows, [['original', 'A']])


class InterfaceTests(unittest.TestCase):
    def setUp(self):
        self.app = MiniTaBom()
        self.addCleanup(self.app.destroy)
        self.app.withdraw()
        # Dados explícitos para os testes de edição e análise.
        from history import WorksheetHistory
        self.app.headers = ['Medição', 'Grupo']
        self.app.rows = [[str(x), 'A'] for x in [10,12,11,14,13,15,12,16,14,13]]
        self.app.history = WorksheetHistory(self.app.headers, self.app.rows)
        self.app.refresh()
        self.app.update_idletasks()

    def start_edit(self, text):
        # A janela fica oculta; a geometria da célula é fornecida só para
        # testar o ciclo de vida de um Entry Tk real, sem captura visual.
        with patch.object(self.app.table, 'bbox', return_value=(52, 50, 166, 27)):
            self.app.worksheet.start_edit(text)

    def test_dialog_center_uses_actual_size_and_parent_monitor(self):
        from unittest.mock import Mock
        dialog = SimpleNamespace(update_idletasks=Mock(), winfo_width=lambda: 1,
                                 winfo_height=lambda: 1, initial_size=(980, 640), winfo_reqwidth=lambda: 2500,
                                 winfo_reqheight=lambda: 1400, geometry=Mock(), winfo_exists=lambda: True,
                                 after=Mock(return_value='test-after'), bind=Mock())
        with patch.object(self.app, 'winfo_rootx', return_value=2500), patch.object(self.app, 'winfo_rooty', return_value=100), \
             patch.object(self.app, 'winfo_width', return_value=1180), patch.object(self.app, 'winfo_height', return_value=790), \
             patch('app.monitor_work_area', return_value=(1920, 0, 3840, 1040)):
            self.app.center_dialog(dialog)
        dialog.geometry.assert_called_once_with('+2600+175')
        dialog.after.assert_called_once()

    def test_destroying_dialog_cancels_deferred_positioning(self):
        dialog = self.app.basic_test_dialog('z')
        pending = dialog._center_after_id
        self.assertIsNotNone(pending)
        dialog.destroy()
        self.assertNotIn(pending, self.app.tk.call('after', 'info'))

    def test_cancel_inline_edit_keeps_data_and_dirty_state(self):
        self.start_edit('999')
        self.app.worksheet.cancel_edit()
        self.assertEqual(self.app.rows[0][0], '10')
        self.assertFalse(self.app.dirty)

    def test_pending_edit_is_saved_without_requiring_enter(self):
        with tempfile.TemporaryDirectory() as directory:
            self.app.project_path = str(Path(directory) / 'sample.statlab')
            self.start_edit('123,5')
            self.assertTrue(self.app.save_project())
            self.assertEqual(load_project(self.app.project_path)[1][0][0], '123,5')
            self.assertIsNone(self.app.worksheet.editor)
            self.assertFalse(self.app.dirty)

    def test_virtual_rows_only_become_data_on_commit(self):
        before = len(self.app.rows)
        self.app.worksheet.select(20, 0)
        self.assertEqual(len(self.app.rows), before)
        self.start_edit('42')
        self.app.worksheet.commit_edit()
        self.assertEqual(len(self.app.rows), 21)
        self.assertEqual(self.app.rows[20], ['42', ''])
        self.assertTrue(self.app.dirty)
        self.assertIn('21 linhas', self.app.dimensions.get())

    def test_tab_wraps_and_analysis_column_tracks_selection(self):
        self.app.worksheet.select(0, 1)
        self.app.worksheet.move_tab(1)
        self.assertEqual(self.app.worksheet.active, (1, 0))
        self.assertEqual(self.app.column.current(), 0)
        self.app.worksheet.move_tab(-1)
        self.assertEqual(self.app.worksheet.active, (0, 1))
        self.assertEqual(self.app.column.current(), 1)

    def test_range_selection_copy_and_clear_restore_in_one_undo(self):
        sheet = self.app.worksheet
        original = [row[:] for row in self.app.rows]
        sheet.select(1, 0)
        sheet.move(2, 1, extend=True)
        self.assertEqual(sheet.selection_bounds, (1, 0, 3, 1))
        with patch.object(sheet, 'clipboard_clear'), patch.object(sheet, 'clipboard_append') as write:
            sheet.copy()
        self.assertEqual(write.call_args.args[0], '12\tA\r\n11\tA\r\n14\tA')
        sheet.clear_selection()
        self.assertEqual(self.app.rows[1:4], [['', ''], ['', ''], ['', '']])
        self.assertEqual(self.app.rows[0], original[0])
        self.app.undo_data()
        self.assertEqual(self.app.rows, original)

    def test_paste_uses_upper_left_of_reverse_selection(self):
        sheet = self.app.worksheet
        sheet.select(3, 1)
        sheet.select(1, 0, extend=True)
        with patch.object(sheet, 'clipboard_get', return_value='X\tY\nZ\tW'):
            sheet.paste()
        self.assertEqual(self.app.rows[1:3], [['X', 'Y'], ['Z', 'W']])
        self.assertEqual(sheet.active, (1, 0))

    def test_drag_selects_cells_and_header_selects_data_column(self):
        sheet, grid = self.app.worksheet, self.app.table
        with patch.object(grid, 'winfo_width', return_value=540), \
             patch.object(grid, 'winfo_height', return_value=280):
            sheet.click(SimpleNamespace(x=60, y=60, state=0))
            sheet.drag(SimpleNamespace(x=180, y=110))
            sheet.release()
            self.assertEqual(sheet.selection_bounds, (0, 0, 2, 1))
            sheet.click(SimpleNamespace(x=210, y=12, state=0))
            self.assertEqual(sheet.selection_bounds, (0, 1, 9, 1))

    def test_resized_columns_keep_cell_coordinates_and_data(self):
        sheet, grid = self.app.worksheet, self.app.table
        original = [row[:] for row in self.app.rows]
        with patch.object(grid, 'winfo_width', return_value=540), \
             patch.object(grid, 'winfo_height', return_value=280):
            sheet.click(SimpleNamespace(x=160, y=12, state=0))
            sheet.drag(SimpleNamespace(x=280, y=12))
            sheet.release()
            self.assertEqual(grid.column_widths[0], 236)
            self.assertEqual(grid.identify_column(270), '#1')
            self.assertEqual(grid.identify_column(290), '#2')
            sheet.select(0, 1)
            self.assertEqual(grid.bbox('0', '1')[0], 280)
            grid.fit_column(0)
            self.assertGreaterEqual(grid.column_widths[0], 60)
        self.assertEqual(self.app.rows, original)
        self.assertFalse(self.app.dirty)

    def test_combobox_selection_survives_pending_cell_commit(self):
        self.start_edit('25')
        self.app.column.current(1)
        self.app.choose_column()
        self.assertEqual(self.app.rows[0][0], '25')
        self.assertEqual(self.app.worksheet.active, (0, 1))
        self.assertEqual(self.app.column.get(), 'Grupo')

    def test_click_row_number_updates_active_cell(self):
        self.app.worksheet.select(0, 1)
        with patch.object(self.app.table, 'identify_row', return_value='7'), \
             patch.object(self.app.table, 'identify_column', return_value='#0'):
            self.app.worksheet.click(SimpleNamespace(x=5, y=100))
        self.assertEqual(self.app.worksheet.active, (7, 1))
        self.assertEqual(self.app.cell_name.get(), 'C2 · linha 8')

    def test_grid_scroll_keeps_hit_testing_and_editing_on_selected_cell(self):
        self.app.headers = [f'Variável {i}' for i in range(50)]
        self.app.rows = [[''] * 50 for _ in range(5000)]
        self.app.rows[4500][35] = 'valor original'
        self.app.refresh()
        grid = self.app.table
        with patch.object(grid, 'winfo_width', return_value=540), \
             patch.object(grid, 'winfo_height', return_value=280):
            self.app.worksheet.select(4500, 35)
            grid.redraw()
            x, y, w, h = grid.bbox('4500', '35')
            self.assertEqual(grid.identify_row(y + h // 2), '4500')
            self.assertEqual(grid.identify_column(x + w // 2), '#36')
            self.assertEqual(grid.identify_row(12), '')
            self.assertEqual(grid.identify_region(x, 36), 'heading')
            # A planilha grande não deve criar um item gráfico para cada dado.
            self.assertLess(len(grid.find_all()), 500)
            self.app.worksheet.start_edit('alterado')
            self.app.worksheet.commit_edit()
        self.assertEqual(self.app.rows[4500][35], 'alterado')
        self.assertEqual(self.app.rows[0][0], '')

    def test_project_manager_can_be_shown_and_hidden_without_losing_results(self):
        self.assertNotIn(str(self.app.sidebar), self.app.workspace.panes())
        self.app.run_summary([0], ['Soma'])
        before = self.app.navigator.get_children('results')
        self.app.show_project.set(True)
        self.app.toggle_project()
        self.assertIn(str(self.app.sidebar), self.app.workspace.panes())
        self.app.show_project.set(False)
        self.app.toggle_project()
        self.assertNotIn(str(self.app.sidebar), self.app.workspace.panes())
        self.assertEqual(self.app.navigator.get_children('results'), before)

    def test_active_title_follows_the_actual_pane(self):
        self.app.highlight_pane(SimpleNamespace(widget=self.app.table))
        self.assertEqual(self.app.grid_title.cget('foreground'), 'white')
        self.assertNotEqual(self.app.session_title.cget('foreground'), 'white')
        self.app.highlight_pane(SimpleNamespace(widget=self.app.output))
        self.assertEqual(self.app.session_title.cget('foreground'), 'white')
        self.assertNotEqual(self.app.grid_title.cget('foreground'), 'white')

    def test_analysis_commits_cell_before_calculating(self):
        self.start_edit('20')
        self.assertTrue(self.app.run_summary([0], ['Soma']))
        self.assertIn('Soma: 140', self.app.output.get('1.0', 'end'))
        self.assertEqual(self.app.rows[0][0], '20')

    def test_new_project_resets_and_has_no_fake_observations(self):
        with patch.object(self.app, 'confirm_replace', return_value=True):
            self.app.new_project()
        self.assertEqual(self.app.rows, [])
        self.assertEqual(len(self.app.headers), 3)
        self.assertEqual(self.app.output.get('1.0', 'end-1c'), '')
        self.assertFalse(self.app.dirty)

    def test_rename_preserves_data_and_active_column(self):
        self.app.worksheet.select(3, 1)
        with patch('app.simpledialog.askstring', return_value='Turma'):
            self.app.rename_column(1)
        self.assertEqual(self.app.headers, ['Medição', 'Turma'])
        self.assertEqual(self.app.rows[3], ['14', 'A'])
        self.assertEqual(self.app.worksheet.active, (3, 1))
        self.assertTrue(self.app.dirty)

    def test_undo_redo_pending_cell_and_column_addition(self):
        self.start_edit('99')
        self.app.undo_data()
        self.assertEqual(self.app.rows[0][0], '10')
        self.app.redo_data()
        self.assertEqual(self.app.rows[0][0], '99')
        with patch('app.simpledialog.askstring', return_value='Nova'):
            self.app.add_column()
        self.assertEqual(len(self.app.headers), 3)
        self.app.undo_data()
        self.assertEqual(len(self.app.headers), 2)
        self.assertTrue(all(len(row) == 2 for row in self.app.rows))
        self.app.redo_data()
        self.assertEqual(self.app.headers[-1], 'Nova')

    def test_graph_snapshot_and_both_renderers(self):
        values = [1, 2, 3, 4, 5, 100]
        for kind in ('Histograma', 'Boxplot'):
            graph = GraphWindow(self.app, kind, 'A', values)
            try:
                graph.withdraw()
                graph.canvas.configure(width=700, height=400)
                self.app.update_idletasks()
                graph.draw()
                self.assertGreater(len(graph.canvas.find_all()), 10)
                self.assertIsNot(graph.values, values)
                self.assertEqual(graph.values, values)
            finally:
                graph.destroy()

    def test_ttest_dialog_submits_and_adds_navigator_result(self):
        dialog = self.app.ttest_dialog('one')
        self.assertEqual(dialog.first.current(), 0)
        dialog.null.delete(0, 'end')
        dialog.null.insert(0, '13')
        dialog.submit()
        self.assertFalse(dialog.winfo_exists())
        output = self.app.output.get('1.0', 'end')
        self.assertIn('T DE UMA AMOSTRA', output)
        self.assertIn('Valor-p = 1', output)
        self.assertTrue(self.app.navigator.get_children('results'))

    def test_ttest_summary_dialogs_and_confidence_only(self):
        for mode in ('one', 'paired', 'two'):
            with self.subTest(mode=mode):
                dialog = self.app.ttest_dialog(mode)
                dialog.source.current(1)
                dialog.toggle_source()
                self.assertFalse(dialog.column_frame.winfo_manager())
                self.assertEqual(dialog.summary_frame.winfo_manager(), 'grid')
                for entries in dialog.summary_entries:
                    for key, text in dict(n='6', mean='2,5', sd='1,2').items():
                        entries[key].insert(0, text)
                dialog.perform_test.set(False)
                dialog.toggle_test()
                start = self.app.output.index('end-1c')
                dialog.submit()
                self.assertFalse(dialog.winfo_exists())
                output = self.app.output.get(start, 'end')
                self.assertIn('dados resumidos', output)
                self.assertIn('IC de 95%', output)
                self.assertNotIn('Valor-p', output)

    def test_ttest_stacked_dialog_submits(self):
        self.app.headers = ['Resposta', 'Grupo']
        self.app.rows = [['1', 'A'], ['2', 'A'], ['3', 'A'], ['4', 'B'], ['6', 'B'], ['8', 'B']]
        self.app.refresh()
        dialog = self.app.ttest_dialog('two')
        dialog.source.current(2)
        dialog.toggle_source()
        self.assertEqual(dialog.first_label.cget('text'), 'Resposta:')
        self.assertEqual(dialog.second_label.cget('text'), 'Grupo:')
        dialog.first.current(0)
        dialog.second.current(1)
        dialog.submit()
        self.assertFalse(dialog.winfo_exists())
        output = self.app.output.get('1.0', 'end')
        self.assertIn("grupo 'A'", output)
        self.assertIn('Estimativa: -4', output)
        self.assertTrue(self.app.navigator.get_children('results'))

    def test_invalid_ttest_summary_keeps_dialog_and_session(self):
        dialog = self.app.ttest_dialog('one')
        dialog.source.current(1)
        dialog.toggle_source()
        for key, value in dict(n='3', mean='1', sd='-2').items():
            dialog.summary_entries[0][key].insert(0, value)
        before = self.app.output.get('1.0', 'end')
        with patch('app.messagebox.showerror') as error:
            dialog.submit()
            error.assert_called_once()
        self.assertTrue(dialog.winfo_exists())
        self.assertEqual(before, self.app.output.get('1.0', 'end'))
        dialog.destroy()

    def test_z_dialog_column_and_summary_with_icons_and_report(self):
        dialog = self.app.basic_test_dialog('z')
        dialog.sigma.insert(0, '2')
        dialog.null.delete(0, 'end')
        dialog.null.insert(0, '13')
        dialog.submit()
        self.assertFalse(dialog.winfo_exists())
        self.assertIn('Z DE UMA AMOSTRA — Medição', self.app.output.get('1.0', 'end'))
        self.assertIn('Valor-p = 1', self.app.output.get('1.0', 'end'))
        dialog = self.app.basic_test_dialog('z')
        dialog.source.current(1)
        dialog.toggle_source()
        dialog.n.insert(0, '25')
        dialog.value.insert(0, '12')
        dialog.sigma.insert(0, '5')
        dialog.perform_test.set(False)
        dialog.toggle_test()
        self.assertTrue(dialog.null.instate(['disabled']))
        dialog.submit()
        self.assertFalse(dialog.winfo_exists())
        self.assertIn('Z DE UMA AMOSTRA — Dados resumidos', self.app.output.get('1.0', 'end'))
        self.assertEqual(len(self.app.navigator.get_children('results')), 2)

    def test_proportion_dialog_event_summary_and_invalid_input_atomicity(self):
        dialog = self.app.basic_test_dialog('proportion')
        dialog.column.current(1)
        dialog.update_events()
        self.assertEqual(dialog.event.get(), 'A')
        dialog.submit()
        self.assertFalse(dialog.winfo_exists())
        self.assertIn('Eventos = 10    Ensaios = 10', self.app.output.get('1.0', 'end'))
        dialog = self.app.basic_test_dialog('proportion')
        dialog.source.current(1)
        dialog.toggle_source()
        dialog.n.insert(0, '10')
        dialog.value.insert(0, '11')
        before = self.app.output.get('1.0', 'end')
        with patch('app.messagebox.showerror') as error:
            dialog.submit()
            error.assert_called_once()
        self.assertTrue(dialog.winfo_exists())
        self.assertEqual(self.app.output.get('1.0', 'end'), before)
        dialog.value.delete(0, 'end')
        dialog.value.insert(0, '4')
        dialog.method.current(1)
        dialog.submit()
        self.assertFalse(dialog.winfo_exists())
        self.assertIn('IC Wilson', self.app.output.get('1.0', 'end'))

    def test_sort_dialog_is_one_undo_step_and_invalidates_regression(self):
        from history import WorksheetHistory
        self.load_linear_sample()
        self.app.history = WorksheetHistory(self.app.headers, self.app.rows)
        original = [r[:] for r in self.app.rows]
        self.app.run_regression(1, [0], show_graph=False)
        dialog = self.app.data_operation_dialog('sort')
        dialog.keys[0].current(1)
        dialog.directions[0].current(1)
        dialog.submit()
        self.assertFalse(dialog.winfo_exists())
        self.assertEqual(self.app.rows, original[::-1])
        self.assertEqual(self.app.history.position, 1)
        self.assertIsNone(self.app.last_regression)
        self.app.undo_data()
        self.assertEqual(self.app.rows, original)
        self.app.redo_data()
        self.assertEqual(self.app.rows, original[::-1])
        self.assertIn('OPERAÇÃO DE DADOS — Ordenar linhas', self.app.output.get('1.0', 'end'))

    def test_stack_and_unstack_dialogs_add_columns_with_single_history_entries(self):
        from history import WorksheetHistory
        self.load_linear_sample()
        self.app.history = WorksheetHistory(self.app.headers, self.app.rows)
        original = [r[:] for r in self.app.rows]
        dialog = self.app.data_operation_dialog('stack')
        dialog.columns.selection_set(0, 1)
        dialog.submit()
        self.assertFalse(dialog.winfo_exists())
        self.assertEqual(self.app.headers, ['X', 'Y', 'Valor', 'Origem'])
        self.assertEqual(len(self.app.rows), 10)
        self.assertEqual([r[:2] for r in self.app.rows[:5]], original)
        self.assertEqual(self.app.history.position, 1)
        dialog = self.app.data_operation_dialog('unstack')
        dialog.value_column.current(2)
        dialog.group_column.current(3)
        dialog.submit()
        self.assertFalse(dialog.winfo_exists())
        self.assertEqual([r[-2:] for r in self.app.rows[:5]], original)
        self.assertEqual(self.app.history.position, 2)
        self.app.undo_data()
        self.assertEqual(len(self.app.headers), 4)

    def test_invalid_data_operation_keeps_history_table_and_output(self):
        before = ([r[:] for r in self.app.rows], self.app.output.get('1.0', 'end'), self.app.history.position)
        dialog = self.app.data_operation_dialog('sort')
        dialog.keys[1].current(dialog.keys[0].current())
        with patch('app.messagebox.showerror') as error:
            dialog.submit()
            error.assert_called_once()
        self.assertTrue(dialog.winfo_exists())
        self.assertEqual((self.app.rows, self.app.output.get('1.0', 'end'), self.app.history.position), before)
        dialog.destroy()

    def test_descriptive_dialog_all_statistics_submit(self):
        import tkinter as tk
        self.app.summary_dialog()
        dialog = next(w for w in self.app.winfo_children()
                      if isinstance(w, tk.Toplevel))
        def descendants(widget):
            for child in widget.winfo_children():
                yield child
                yield from descendants(child)
        buttons = {w.cget('text'): w for w in descendants(dialog)
                   if w.winfo_class() == 'TButton'}
        buttons['Selecionar todas'].invoke()
        self.app.update_idletasks()
        self.assertLessEqual(dialog.winfo_reqheight(), self.app.winfo_screenheight())
        buttons['OK'].invoke()
        self.assertFalse(dialog.winfo_exists())
        output = self.app.output.get('1.0', 'end')
        for label in ['Média aparada (5% por ponta)', 'Moda', 'Frequência da moda',
                      'Assimetria', 'Curtose (excesso)', 'MSSD']:
            self.assertIn(label + ':', output)

    def test_grouped_descriptive_dialog_submits_and_indexes_report(self):
        self.app.rows[1][1] = 'B'
        dialog = self.app.summary_dialog()
        dialog.groups.selection_set(1)
        dialog.update_options()
        self.assertFalse(dialog.missing_check.instate(['disabled']))
        self.assertTrue(dialog.empty_check.instate(['disabled']))
        dialog.submit()
        self.assertFalse(dialog.winfo_exists())
        report = self.app.output.get('1.0', 'end')
        self.assertIn('(por Grupo)', report)
        self.assertIn("Grupo: Grupo = 'B'\nN: 1", report)
        self.assertTrue(self.app.navigator.get_children('results'))

    def test_invalid_grouped_summary_keeps_session_and_dialog(self):
        self.app.rows[1] = ['inválido', 'B']
        before = self.app.output.get('1.0', 'end')
        dialog = self.app.summary_dialog()
        dialog.groups.selection_set(1)
        with patch('app.messagebox.showerror') as error:
            dialog.submit()
            error.assert_called_once()
        self.assertTrue(dialog.winfo_exists())
        self.assertEqual(self.app.output.get('1.0', 'end'), before)
        dialog.destroy()

    def test_invalid_ttest_leaves_session_untouched(self):
        before = self.app.output.get('1.0', 'end')
        with patch('app.messagebox.showerror') as error:
            self.assertFalse(self.app.run_ttest('two', 0, 1))
            error.assert_called_once()
        self.assertEqual(self.app.output.get('1.0', 'end'), before)

    def load_linear_sample(self):
        self.app.headers = ['X', 'Y']
        self.app.rows = [[str(x), str(y)] for x, y in zip(range(5), [1, 2, 1, 3, 5])]
        self.app.refresh()

    def test_correlation_dialog_runs_spearman_and_indexes_result(self):
        self.load_linear_sample()
        dialog = self.app.linear_dialog('correlation')
        dialog.method.set('spearman')
        dialog.update_confidence()
        self.assertTrue(dialog.confidence.instate(['disabled']))
        dialog.submit()
        self.assertFalse(dialog.winfo_exists())
        self.assertIn('CORRELAÇÃO DE SPEARMAN', self.app.output.get('1.0', 'end'))
        self.assertTrue(self.app.navigator.get_children('results'))

    def test_regression_dialog_runs_and_indexes_result(self):
        self.load_linear_sample()
        dialog = self.app.linear_dialog('regression')
        dialog.response.current(1)
        dialog.variables.selection_clear(0, 'end')
        dialog.variables.selection_set(0)
        dialog.show_graph.set(False)
        dialog.observations.set(True)
        dialog.submit()
        self.assertFalse(dialog.winfo_exists())
        report = self.app.output.get('1.0', 'end')
        self.assertIn('REGRESSÃO LINEAR — Y', report)
        self.assertIn('Y = 0.6 + 0.9 × X', report)
        self.assertIn('Alavancagem', report)
        self.assertTrue(self.app.navigator.get_children('results'))

    def test_invalid_linear_analysis_does_not_append_partial_output(self):
        before = self.app.output.get('1.0', 'end')
        with patch('app.messagebox.showerror') as error:
            self.assertFalse(self.app.run_correlation([0, 1]))
            self.assertFalse(self.app.run_regression(0, [1], show_graph=False))
            self.assertEqual(error.call_count, 2)
        self.assertEqual(self.app.output.get('1.0', 'end'), before)

    def test_prediction_dialog_submits_and_model_is_invalidated_by_editing(self):
        self.load_linear_sample()
        self.app.run_regression(1, [0], show_graph=False)
        self.assertEqual(self.app.regression_menu.entrycget(1, 'state'), 'normal')
        dialog = self.app.prediction_dialog()
        dialog.values.insert('1.0', '2\n5')
        dialog.submit()
        self.assertFalse(dialog.winfo_exists())
        self.assertIn('PREVISÃO LINEAR — Y', self.app.output.get('1.0', 'end'))
        self.assertIn('Fora da faixa observada: X', self.app.output.get('1.0', 'end'))
        self.start_edit('99')
        self.app.worksheet.commit_edit()
        self.assertIsNone(self.app.last_regression)
        self.assertEqual(self.app.regression_menu.entrycget(1, 'state'), 'disabled')
        before = self.app.output.get('1.0', 'end')
        with patch('app.messagebox.showerror'):
            self.assertFalse(self.app.run_prediction(text='2'))
        self.assertEqual(self.app.output.get('1.0', 'end'), before)

    def test_prediction_from_columns_and_refresh_restores_compatible_model(self):
        self.load_linear_sample()
        self.app.run_regression(1, [0], show_graph=False)
        dialog = self.app.prediction_dialog()
        dialog.tabs.select(1)
        dialog.remember_mode()
        dialog.tabs.select(2)
        dialog.remember_mode()
        self.assertEqual(dialog.input_mode, 'columns')
        dialog.columns[0].current(0)
        dialog.submit()
        self.assertFalse(dialog.winfo_exists())
        self.assertIn('casos de colunas: X', self.app.output.get('1.0', 'end'))
        self.app.refresh()
        self.assertIsNotNone(self.app.last_regression)
        self.assertTrue(self.app.run_prediction(text='2'))

    def test_distribution_dialog_submits_binomial_and_indexes_result(self):
        dialog = self.app.distribution_dialog()
        dialog.distribution.set('Binomial')
        dialog.update_parameters()
        dialog.parameters['n'].delete(0, 'end')
        dialog.parameters['n'].insert(0, '5')
        dialog.value.delete(0, 'end')
        dialog.value.insert(0, '2')
        dialog.submit()
        self.assertFalse(dialog.winfo_exists())
        self.assertIn('DISTRIBUIÇÃO — Binomial', self.app.output.get('1.0', 'end'))
        self.assertIn('P(X ≤ 2) = 0.5', self.app.output.get('1.0', 'end'))
        self.assertTrue(self.app.navigator.get_children('results'))

    def test_menu_icons_preserve_enabled_state_and_commands(self):
        self.assertTrue(self.app.regression_menu.entrycget(0, 'image'))
        self.assertTrue(self.app.regression_menu.entrycget(1, 'image'))
        self.assertEqual(self.app.regression_menu.entrycget(1, 'state'), 'disabled')
        self.app.regression_menu.invoke(0)
        import tkinter as tk
        dialog = next(w for w in self.app.winfo_children() if isinstance(w, tk.Toplevel))
        self.assertEqual(dialog.title(), 'Regressão linear')
        dialog.destroy()

    def test_regression_graph_snapshots_and_renders_simple_and_multiple_models(self):
        self.load_linear_sample()
        result = linear_regression(self.app.headers, self.app.rows, 1, [0])
        graph = RegressionGraph(self.app, result)
        try:
            graph.withdraw()
            graph.draw()
            titles = [graph.canvas.itemcget(i, 'text') for i in graph.canvas.find_all() if graph.canvas.type(i) == 'text']
            self.assertIn('Reta ajustada', titles)
            self.assertIn('Q–Q dos resíduos', titles)
            result['residuals'][0] = 999
            self.assertNotEqual(graph.result['residuals'][0], 999)
        finally:
            graph.destroy()

        rows = [[str(a), str(b), str(2 + 3 * a - 2 * b + .5 * a * b)] for a, b in [(-1, -1), (-1, 1), (1, -1), (1, 1)]]
        multiple = linear_regression(['A', 'B', 'Y'], rows, 2, [0, 1])
        graph = RegressionGraph(self.app, multiple)
        try:
            graph.withdraw()
            graph.draw()
            titles = [graph.canvas.itemcget(i, 'text') for i in graph.canvas.find_all() if graph.canvas.type(i) == 'text']
            self.assertIn('Observados × ajustados', titles)
        finally:
            graph.destroy()

    def test_xy_graph_dialog_scatter_renders_snapshot_and_exports_svg(self):
        import xml.etree.ElementTree as ET
        self.load_linear_sample()
        dialog = self.app.xy_graph_dialog('scatter')
        dialog.y.current(1)
        dialog.x.current(0)
        dialog.connect.set(True)
        dialog.title_value.insert(0, 'Estudo de dispersão')
        dialog.submit()
        self.assertFalse(dialog.winfo_exists())
        graph = next(w for w in self.app.winfo_children() if isinstance(w, XYGraphWindow))
        graph.withdraw()
        graph.draw()
        self.assertEqual(len(graph.canvas.find_withtag('point')), 5)
        self.assertEqual(len(graph.canvas.find_withtag('series')), 1)
        self.app.rows[0][0] = '999'
        self.assertEqual(graph.model['series'][0]['points'][0]['x'], 0)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'scatter.svg'
            self.assertTrue(graph.export_svg(path))
            ET.parse(path)
        graph.destroy()

    def test_time_graph_dialog_and_invalid_log_keeps_dialog_open(self):
        self.load_linear_sample()
        dialog = self.app.xy_graph_dialog('scatter')
        dialog.y.current(1)
        dialog.x.current(0)
        dialog.x_log.set(True)
        with patch('app.messagebox.showerror') as error:
            dialog.submit()
            error.assert_called_once()
        self.assertTrue(dialog.winfo_exists())
        dialog.destroy()
        dialog = self.app.xy_graph_dialog('time')
        self.assertTrue(dialog.connection_check.instate(['disabled']))
        dialog.y.current(1)
        dialog.submit()
        graph = next(w for w in self.app.winfo_children() if isinstance(w, XYGraphWindow))
        graph.draw()
        self.assertEqual(graph.model['x_label'], 'Linha da planilha')
        graph.destroy()

    def test_anova_stacked_dialog_submits_and_indexes_report(self):
        self.app.headers = ['Resposta', 'Grupo']
        self.app.rows = [['1', 'A'], ['2', 'A'], ['3', 'A'], ['4', 'B'], ['5', 'B'], ['6', 'B']]
        self.app.refresh()
        dialog = self.app.anova_dialog()
        dialog.selector.layout_mode.set('stacked')
        dialog.selector.show_mode()
        dialog.submit()
        self.assertFalse(dialog.winfo_exists())
        self.assertIn('ANOVA DE UM FATOR', self.app.output.get('1.0', 'end'))
        self.assertTrue(self.app.navigator.get_children('results'))

    def test_group_boxplots_keep_snapshot_and_show_labels(self):
        prepared, _ = prepare_groups(['A', 'B'], [['1', '4'], ['2', '5'], ['3', '6']], columns=[0, 1])
        graph = GroupGraphWindow(self.app, prepared)
        try:
            graph.withdraw()
            graph.draw()
            labels = [graph.canvas.itemcget(item, 'text') for item in graph.canvas.find_all() if graph.canvas.type(item) == 'text']
            self.assertIn('A', labels)
            self.assertIn('B', labels)
            prepared[0]['values'][0] = 1000
            self.assertEqual(graph.groups[0]['values'], [1, 2, 3])
        finally:
            graph.destroy()

    def test_invalid_anova_does_not_append_partial_output(self):
        before = self.app.output.get('1.0', 'end')
        with patch('app.messagebox.showerror') as error:
            self.assertFalse(self.app.run_anova(columns=[0, 1]))
            error.assert_called_once()
        self.assertEqual(self.app.output.get('1.0', 'end'), before)


if __name__ == '__main__':
    unittest.main()
