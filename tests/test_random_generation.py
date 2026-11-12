from copy import deepcopy
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, Mock

from analysis_service import rerun_analysis
from project import save_document, load_document
from random_contract import RANDOM_DISTRIBUTIONS, MAX_SEED, MAX_INTEGER, validate_random_result
from random_service import execute_random, random_columns
from workspace_model import new_document, active_sheet, sync_sheet, validate_document, is_stale


class RandomGenerationTests(unittest.TestCase):
    def setUp(self):
        self.document = new_document(['Original'], [['A'], ['B']])
        self.sheet = active_sheet(self.document)

    def generate(self, name='Normal', parameters=None, **options):
        parameters = {'mean': 0., 'sd': 1.} if parameters is None else parameters
        return execute_random(self.sheet, name, parameters, row_count=options.pop('row_count', 12),
                              seed=options.pop('seed', 123), **options)

    def test_fourteen_families_dimensions_support_and_seed_reproduction(self):
        for name, schema in RANDOM_DISTRIBUTIONS.items():
            parameters = {key: value for key, _, value in schema}
            with self.subTest(distribution=name):
                a = self.generate(name, parameters, column_count=2)
                b = self.generate(name, parameters, column_count=2)
                c = self.generate(name, parameters, column_count=2, seed=456)
                self.assertEqual(a['values'], b['values'])
                self.assertNotEqual(a['values'], c['values'])
                self.assertEqual([len(col) for col in a['values']['columns']], [12, 12])
                validate_random_result(a)
                self.assertEqual(a['provenance']['generation']['engine'], 'PCG64')
                self.assertEqual(a['provenance']['reference16'], 'pending')

    def test_degenerate_distributions_have_exact_integer_outputs(self):
        cases = [('Bernoulli', {'p': 0}, 0), ('Bernoulli', {'p': 1}, 1),
                 ('Binomial', {'n': 0, 'p': .8}, 0), ('Binomial', {'n': 8, 'p': 0}, 0),
                 ('Binomial', {'n': 8, 'p': 1}, 8), ('Poisson', {'mean': 0}, 0),
                 ('Inteiros', {'lower': MAX_INTEGER, 'upper': MAX_INTEGER}, MAX_INTEGER),
                 ('Inteiros', {'lower': -MAX_INTEGER, 'upper': -MAX_INTEGER}, -MAX_INTEGER)]
        for name, parameters, expected in cases:
            with self.subTest(name=name, parameters=parameters):
                r = self.generate(name, parameters)
                self.assertTrue(all(type(x) is int and x == expected for x in r['values']['columns'][0]))

    def test_integer_bounds_are_inclusive_and_seed_accepts_128_bits(self):
        r = self.generate('Inteiros', {'lower': -2, 'upper': 2}, row_count=200, seed=MAX_SEED)
        self.assertEqual(set(r['values']['columns'][0]), {-2, -1, 0, 1, 2})
        self.assertEqual(r['parameters']['seed'], MAX_SEED)

    def test_generation_does_not_change_numpy_global_random_state(self):
        from inference import scientific_stats
        scientific_stats()
        import numpy as np
        before = np.random.get_state()
        self.generate()
        after = np.random.get_state()
        self.assertEqual(before[0], after[0])
        self.assertTrue(np.array_equal(before[1], after[1]))
        self.assertEqual(before[2:], after[2:])

    def test_blank_seed_is_chosen_once_and_recorded(self):
        with patch('random_service.secrets.randbits', return_value=MAX_SEED) as entropy:
            r = self.generate(seed=None)
        entropy.assert_called_once_with(128)
        self.assertEqual(r['parameters']['seed'], MAX_SEED)
        self.assertEqual(r['values'], self.generate(seed=MAX_SEED)['values'])

    def test_invalid_parameters_and_sizes_fail_before_drawing(self):
        cases = [dict(row_count=0), dict(row_count=200001), dict(row_count=True), dict(column_count=0),
                 dict(column_count=513), dict(column_count=1.5), dict(seed=-1), dict(seed=MAX_SEED + 1),
                 dict(seed=True), dict(seed=1.), dict(base_name='  '), dict(distribution='Unknown'),
                 dict(distribution_parameters={'mean': 0, 'sd': 0}),
                 dict(distribution_parameters={'mean': math.inf, 'sd': 1}),
                 dict(distribution_parameters={'mean': True, 'sd': 1}),
                 dict(distribution_parameters={'mean': 0}),
                 dict(distribution='Bernoulli', distribution_parameters={'p': 1.1}),
                 dict(distribution='Inteiros', distribution_parameters={'lower': .1, 'upper': 3}),
                 dict(distribution='Inteiros', distribution_parameters={'lower': 4, 'upper': 3}),
                 dict(distribution='Inteiros', distribution_parameters={'lower': 0, 'upper': 2**53}),
                 dict(distribution='Lognormal', distribution_parameters={'meanlog': 1000, 'sdlog': 1}),
                 dict(distribution='Uniforme', distribution_parameters={'lower': -1e308, 'upper': 1e308})]
        original = deepcopy(self.sheet)
        with patch('random_service.scientific_stats') as backend:
            for changes in cases:
                options = dict(distribution='Normal', distribution_parameters={'mean': 0, 'sd': 1}, row_count=12, seed=123)
                options.update(changes)
                with self.subTest(changes=changes), self.assertRaises(ValueError):
                    execute_random(self.sheet, **options)
            backend.assert_not_called()
        self.assertEqual(self.sheet, original)

    def test_capacity_includes_existing_data_before_drawing_or_replaying(self):
        r = self.generate(row_count=3)
        self.document['analyses'].append(r)
        original = deepcopy(self.document)
        with patch('random_contract.MAX_CELLS', 5), patch('random_service.scientific_stats') as backend:
            with self.assertRaises(ValueError): self.generate(row_count=3)
            with self.assertRaises(ValueError): rerun_analysis(self.document, r['analysis_id'])
            backend.assert_not_called()
        self.assertEqual(self.document, original)

    def test_nonfinite_draw_fails_before_changing_any_data(self):
        from inference import scientific_stats
        scientific_stats()
        import numpy as np
        sampler = Mock()
        sampler.rvs.return_value = np.array([[math.inf] * 12])
        original = deepcopy(self.sheet)
        with patch('random_service.frozen_distribution', return_value=(sampler, False, {})), self.assertRaises(ValueError):
            self.generate()
        self.assertEqual(self.sheet, original)

    def test_append_expands_rows_without_overwriting_and_resolves_names(self):
        r = self.generate('Inteiros', {'lower': 7, 'upper': 7}, row_count=3, column_count=2, base_name='Original')
        headers, rows, names = random_columns(['Original', 'Original 1'], [['A', 'B']], r)
        self.assertEqual(names, ['Original 1 (2)', 'Original 2'])
        self.assertEqual(rows, [['A', 'B', '7', '7'], ['', '', '7', '7'], ['', '', '7', '7']])
        self.assertEqual(headers[:2], ['Original', 'Original 1'])
        shorter = self.generate('Inteiros', {'lower': 8, 'upper': 8}, row_count=1, base_name='Original')
        headers, rows, names = random_columns(['Original'], self.sheet['rows'], shorter)
        self.assertEqual(names, ['Original (2)'])
        self.assertEqual(rows, [['A', '8'], ['B', '']])

    def test_roundtrip_replays_saved_values_without_calling_sampler(self):
        r = self.generate(column_count=2)
        self.document['analyses'].append(r)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'random.statlab'
            save_document(path, self.document)
            loaded = load_document(path)
        sheet = active_sheet(loaded)
        sync_sheet(sheet, ['Other'], [['edited']])
        self.assertFalse(is_stale(r, sheet))
        with patch('random_service.execute_random', side_effect=AssertionError('must not draw')):
            replay = rerun_analysis(loaded, r['analysis_id'])
        self.assertEqual(replay['values'], r['values'])
        self.assertIsNot(replay['values']['columns'], r['values']['columns'])
        self.assertEqual(replay['parameters'], r['parameters'])
        self.assertEqual(replay['provenance']['generation'], r['provenance']['generation'])
        self.assertEqual(replay['provenance']['execution'], 'replay_saved_values')
        self.assertEqual(replay['parent_analysis_id'], r['analysis_id'])
        self.assertNotEqual(replay['analysis_id'], r['analysis_id'])
        loaded['analyses'].append(replay)
        validate_document(loaded)

    def test_corrupted_history_is_rejected_before_replacing_saved_project(self):
        self.document['analyses'].append(self.generate())
        def wrong_count(r): r['values']['columns'][0].pop()
        def nan(r): r['values']['columns'][0][0] = math.nan
        def bool_seed(r): r['parameters']['seed'] = True
        def wrong_kind(r): r['source']['kind'] = 'columns'
        def wrong_engine(r): r['provenance']['generation']['engine'] = 'unknown'
        def float_discrete(r):
            r['parameters'].update(distribution='Bernoulli', distribution_parameters={'p': .5})
            r['values'].update(discrete=True, columns=[[.5] * 12])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'saved.statlab'
            save_document(path, self.document)
            original = path.read_bytes()
            for change in [wrong_count, nan, bool_seed, wrong_kind, wrong_engine, float_discrete]:
                bad = deepcopy(self.document)
                change(bad['analyses'][0])
                with self.subTest(change=change.__name__), self.assertRaises(ValueError): save_document(path, bad)
                self.assertEqual(path.read_bytes(), original)


class RandomInterfaceTests(unittest.TestCase):
    def setUp(self):
        from app import MiniTaBom
        self.app = MiniTaBom()
        self.app.withdraw()
        self.addCleanup(self.app.destroy)
        self.app.headers = ['Original']
        self.app.rows = [['A'], ['B']]
        self.app.refresh()
        from history import WorksheetHistory
        sheet = active_sheet(self.app.document)
        self.app.history = WorksheetHistory(self.app.headers, self.app.rows, columns=sheet['columns'])
        self.app.sheet_histories[sheet['id']] = self.app.history

    def generate(self, **options):
        return self.app.run_random('Normal', {'mean': 10., 'sd': 2.}, row_count=4, column_count=2, seed=42, **options)

    def test_menu_dialog_decimal_input_and_128_bit_seed(self):
        dialog = self.app.random_dialog()
        for control, value in [(dialog.parameters['mean'], '10,5'), (dialog.parameters['sd'], '2,5'),
                               (dialog.row_count, '3'), (dialog.column_count, '2'), (dialog.seed, str(MAX_SEED)),
                               (dialog.base_name, 'Teste')]:
            control.delete(0, 'end'); control.insert(0, value)
        dialog.submit()
        self.assertFalse(dialog.winfo_exists())
        from tests.task_helpers import drain_task
        drain_task(self.app)
        r = self.app.document['analyses'][-1]
        self.assertEqual(r['parameters']['distribution_parameters'], {'mean': 10.5, 'sd': 2.5})
        self.assertEqual(r['parameters']['seed'], MAX_SEED)
        self.assertEqual(r['storage']['names'], ['Teste 1', 'Teste 2'])
        self.assertTrue(any('DADOS ALEATÓRIOS' in self.app.navigator.item(k, 'text') for k in self.app.navigator.get_children('results')))
        menu = self.app.nametowidget(self.app.cget('menu'))
        calc = next(self.app.nametowidget(menu.entrycget(i, 'menu')) for i in range(menu.index('end') + 1)
                    if menu.type(i) == 'cascade' and menu.entrycget(i, 'label') == 'Calc')
        self.assertIn('Dados aleatórios…', [calc.entrycget(i, 'label') for i in range(calc.index('end') + 1)])

    def test_undo_redo_is_single_step_and_preserves_column_ids(self):
        before_columns = deepcopy(active_sheet(self.app.document)['columns'])
        self.assertTrue(self.generate())
        after_headers, after_rows = list(self.app.headers), deepcopy(self.app.rows)
        generated_columns = deepcopy(active_sheet(self.app.document)['columns'])
        self.app.undo_data()
        self.assertEqual((self.app.headers, self.app.rows), (['Original'], [['A'], ['B']]))
        self.assertEqual(active_sheet(self.app.document)['columns'], before_columns)
        self.assertEqual(len(self.app.document['analyses']), 1)
        self.app.redo_data()
        self.assertEqual((self.app.headers, self.app.rows), (after_headers, after_rows))
        self.assertEqual(active_sheet(self.app.document)['columns'], generated_columns)

    def test_reopen_and_history_replay_keeps_exact_cell_text_and_old_result(self):
        self.assertTrue(self.generate())
        old = deepcopy(self.app.document['analyses'][-1])
        expected = [row[-2:] for row in self.app.rows]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'random.statlab'
            self.app.project_path = str(path)
            self.assertTrue(self.app.save_project())
            with patch('app.filedialog.askopenfilename', return_value=str(path)):
                self.app.open_project()
            history = self.app.analysis_history_dialog()
            self.assertEqual(history.rerun_button.cget('text'), 'Reproduzir valores salvos')
            self.assertEqual(history.tree.item(old['analysis_id'], 'values')[-1], 'Valores salvos')
            history.rerun()
            export = Path(directory) / 'result.json'
            with patch('analysis_history_dialog.filedialog.asksaveasfilename', return_value=str(export)):
                history.export()
            import json
            self.assertEqual(json.loads(export.read_text(encoding='utf-8'))['values'], old['values'])
            history.destroy()
        self.assertEqual([row[-2:] for row in self.app.rows], expected)
        self.assertEqual(self.app.document['analyses'][0], old)
        self.assertEqual(self.app.document['analyses'][-1]['storage']['names'], ['Aleatorio 1 (2)', 'Aleatorio 2 (2)'])
        self.app.sync_document()
        validate_document(self.app.document)

    def test_replay_on_inactive_sheet_preserves_active_data_and_undo(self):
        self.assertTrue(self.generate())
        origin = active_sheet(self.app.document)['id']
        old_id = self.app.document['analyses'][-1]['analysis_id']
        self.app.add_worksheet('Outra')
        current_id = active_sheet(self.app.document)['id']
        current_data = (list(self.app.headers), deepcopy(self.app.rows))
        self.assertTrue(self.app.rerun_saved_analysis(old_id))
        self.assertEqual(self.app.document['active_worksheet_id'], current_id)
        self.assertEqual((self.app.headers, self.app.rows), current_data)
        self.app.switch_worksheet(origin)
        self.assertEqual(len(self.app.headers), 5)
        self.app.undo_data()
        self.assertEqual(len(self.app.headers), 3)
        self.app.redo_data()
        self.assertEqual(len(self.app.headers), 5)

    def test_invalid_generation_does_not_change_data_history_or_session(self):
        self.app.sync_document()
        before = deepcopy(self.app.document)
        output = self.app.output.get('1.0', 'end')
        with patch('app.messagebox.showerror'):
            self.assertFalse(self.app.run_random('Normal', {'mean': 0., 'sd': -1.}, row_count=4))
        self.assertEqual(self.app.document, before)
        self.assertEqual(self.app.output.get('1.0', 'end'), output)
        self.assertIsNone(self.app.history.undo())

    def test_corrupt_project_is_rejected_without_replacing_open_work(self):
        self.assertTrue(self.generate())
        self.app.sync_document()
        before = deepcopy(self.app.document)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'corrupt.statlab'
            bad = deepcopy(before)
            bad['analyses'][0]['values']['columns'][0].pop()
            import json
            path.write_text(json.dumps(bad), encoding='utf-8')
            with patch('app.filedialog.askopenfilename', return_value=str(path)), patch('app.messagebox.showerror'):
                self.app.open_project()
        self.assertEqual(self.app.document, before)
