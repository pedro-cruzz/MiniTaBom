from copy import deepcopy
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from background_tasks import BackgroundTask, TaskContext, TaskCancelled
from excel_import import read_excel_workbook, _table
from random_service import execute_random
from tests.task_helpers import drain_task
from tests.test_excel_open import write_book
from workspace_model import active_sheet, new_document


class BackgroundTaskTests(unittest.TestCase):
    def wait(self, task):
        task.thread.join(5.)
        self.assertFalse(task.thread.is_alive())

    def test_work_runs_outside_caller_and_outcome_is_consumed_once(self):
        caller = threading.get_ident()
        task = BackgroundTask(lambda context: threading.get_ident())
        self.wait(task)
        state, worker = task.take_outcome()
        self.assertEqual(state, 'succeeded')
        self.assertNotEqual(caller, worker)
        self.assertIsNone(task.take_outcome())
        self.assertFalse(task.cancel())

    def test_cancellation_during_work_discards_partial_result(self):
        started = threading.Event()
        def work(context):
            started.set()
            while True:
                context.cancelled.wait(.005)
                context.checkpoint()
        task = BackgroundTask(work)
        self.assertTrue(started.wait(2.))
        self.assertTrue(task.cancel())
        self.wait(task)
        self.assertEqual(task.take_outcome(), ('cancelled', None))

    def test_cancel_after_worker_finishes_wins_before_delivery(self):
        task = BackgroundTask(lambda context: ['prepared data'])
        self.wait(task)
        self.assertTrue(task.cancel())
        self.assertEqual(task.take_outcome(), ('cancelled', None))

    def test_error_is_delivered_without_unhandled_worker_exception(self):
        def work(context): raise ValueError('invalid input')
        task = BackgroundTask(work)
        self.wait(task)
        state, error = task.take_outcome()
        self.assertEqual(state, 'failed')
        self.assertIsInstance(error, ValueError)

    def test_progress_coalesces_and_phase_progress_is_monotonic(self):
        def work(context):
            first = context.phase(0., .6)
            for index in range(10001): first.report(index / 10000, 'working')
            context.report(.3, 'older update')
            context.phase(.6, 1.).report(1., 'ready')
        task = BackgroundTask(work)
        self.wait(task)
        self.assertEqual((task.snapshot()['fraction'], task.snapshot()['message']), (1., 'ready'))
        task.take_outcome()

    def test_cancelled_context_prevents_even_opening_the_file(self):
        event = threading.Event(); event.set()
        with self.assertRaises(TaskCancelled): read_excel_workbook('does-not-exist.xlsx', TaskContext(event))


class CancellableServicesTests(unittest.TestCase):
    def test_all_random_streams_match_previous_joint_sampler_across_chunks(self):
        from inference import scientific_stats
        scientific_stats()
        import numpy as np
        from distributions import frozen_distribution
        from random_contract import RANDOM_DISTRIBUTIONS
        sheet = active_sheet(new_document())
        for name, schema in RANDOM_DISTRIBUTIONS.items():
            with self.subTest(distribution=name):
                parameters = {key: value for key, _, value in schema}
                rng = np.random.Generator(np.random.PCG64(2718))
                if name == 'Inteiros': expected = rng.integers(1, 7, size=(2, 4097))
                elif name == 'Bernoulli': expected = rng.binomial(1, .5, size=(2, 4097))
                else: expected = frozen_distribution(name, parameters)[0].rvs(size=(2, 4097), random_state=rng)
                result = execute_random(sheet, name, parameters, row_count=4097, column_count=2, seed=2718)
                self.assertEqual(result['values']['columns'], expected.tolist())

    def test_cancel_between_draw_chunks_returns_no_result_and_changes_no_sheet(self):
        event = threading.Event()
        def report(fraction, message):
            if fraction > 0: event.set()
        sheet = active_sheet(new_document())
        original = deepcopy(sheet)
        with self.assertRaises(TaskCancelled):
            execute_random(sheet, 'Normal', {'mean': 0, 'sd': 1}, row_count=10000, seed=1,
                           context=TaskContext(event, report))
        self.assertEqual(sheet, original)

    def test_excel_cancel_during_reading_closes_archive_and_can_reopen(self):
        event = threading.Event()
        def report(fraction, message):
            if fraction > .2: event.set()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'book.xlsx'; write_book(path)
            with self.assertRaises(TaskCancelled): read_excel_workbook(path, TaskContext(event, report))
            renamed = path.with_name('renamed.xlsx'); path.rename(renamed)
            self.assertEqual(read_excel_workbook(renamed)['active_name'], 'Dados')

    def test_excel_cancel_while_building_rows_does_not_return_partial_table(self):
        event = threading.Event()
        def report(fraction, message):
            if fraction >= .1: event.set()
        cells = {(i, 1): str(i) for i in range(1, 1001)}
        with self.assertRaises(TaskCancelled):
            _table(cells, {}, 'Dados', automatic=True, context=TaskContext(event, report))
        self.assertEqual(len(cells), 1000)


class BackgroundInterfaceTests(unittest.TestCase):
    def setUp(self):
        from app import MiniTaBom
        self.app = MiniTaBom(); self.app.withdraw()
        self.addCleanup(self.cleanup)
        self.app.headers = ['Original']; self.app.rows = [['A'], ['B']]
        self.app.data_changed(); self.app.refresh(); self.app.sync_document()
        self.callback_errors = []
        self.app.report_callback_exception = lambda *error: self.callback_errors.append(error)

    def cleanup(self):
        if self.app is not None: self.app.destroy()

    def random(self):
        return self.app.start_random('Normal', {'mean': 0, 'sd': 1}, row_count=20, column_count=2, seed=42)

    def test_tk_heartbeat_and_apply_callback_stay_on_main_thread(self):
        main = threading.get_ident(); heartbeat = []; applied = []
        release = threading.Event()
        def work(context):
            while not release.wait(.005): context.checkpoint()
            return threading.get_ident()
        def apply_result(worker): applied.append((worker, threading.get_ident()))
        self.assertTrue(self.app.start_background_task('Teste', work, apply_result))
        self.app.after(20, lambda: (heartbeat.append(threading.get_ident()), release.set()))
        drain_task(self.app)
        self.assertEqual(heartbeat, [main])
        self.assertNotEqual(applied[0][0], main)
        self.assertEqual(applied[0][1], main)
        self.assertEqual(self.callback_errors, [])

    def test_async_random_success_undo_redo_and_progress_dialog(self):
        before = deepcopy(self.app.rows)
        self.assertTrue(self.random())
        dialog = self.app._task_window
        self.assertTrue(dialog.progress.winfo_exists())
        self.assertFalse(self.random())
        drain_task(self.app)
        self.assertEqual(len(self.app.headers), 3)
        self.assertEqual(len(self.app.document['analyses']), 1)
        self.app.undo_data(); self.assertEqual(self.app.rows, before)
        self.app.redo_data(); self.assertEqual(len(self.app.headers), 3)
        self.assertEqual(self.callback_errors, [])

    def test_worker_start_failure_restores_menu_without_leaving_a_task_window(self):
        menu = self.app.nametowidget(self.app.cget('menu'))
        form = self.app.random_dialog()
        with patch('task_dialog.BackgroundTask', side_effect=RuntimeError('thread unavailable')), patch('app.messagebox.showerror'):
            self.assertFalse(self.random())
        self.assertIsNone(self.app._task_window)
        self.assertEqual(menu.entrycget('Arquivo', 'state'), 'normal')
        self.assertIs(self.app.grab_current(), form)
        form.destroy()
        self.assertEqual(self.callback_errors, [])

    def test_cancellation_before_delivery_preserves_all_project_data_and_history(self):
        before = deepcopy(self.app.document)
        history_size = len(self.app.history.states)
        self.assertTrue(self.random())
        dialog = self.app._task_window
        dialog.task.thread.join(3.)
        self.assertFalse(dialog.task.thread.is_alive())
        dialog.cancel_button.invoke()
        drain_task(self.app)
        self.assertEqual(self.app.document, before)
        self.assertEqual(len(self.app.history.states), history_size)
        self.assertIn('cancelada', self.app.status.get())
        self.assertEqual(self.callback_errors, [])

    def test_stale_random_snapshot_is_not_applied_over_new_edits(self):
        self.assertTrue(self.random())
        self.app._task_window.task.thread.join(3.)
        self.app.rows[0][0] = 'changed'; self.app.data_changed(); self.app.sync_document()
        changed = deepcopy(self.app.document)
        with patch('task_dialog.messagebox.showerror') as error: drain_task(self.app)
        error.assert_called_once()
        self.assertEqual(self.app.document, changed)
        self.assertEqual(self.callback_errors, [])

    def test_async_generation_into_original_inactive_sheet(self):
        original = active_sheet(self.app.document)['id']
        self.assertTrue(self.random())
        self.app.add_worksheet('Outra')
        current = active_sheet(self.app.document)['id']
        drain_task(self.app)
        self.assertEqual(active_sheet(self.app.document)['id'], current)
        self.assertEqual(self.app.rows, [])
        self.app.switch_worksheet(original)
        self.assertEqual(len(self.app.headers), 3)

    def test_excel_menu_reads_in_worker_and_keeps_automatic_opening(self):
        from excel_import import read_excel_workbook as read
        threads = []
        def worker_read(path, context):
            threads.append(threading.get_ident()); return read(path, context)
        self.app.dirty = False
        menu = self.app.nametowidget(self.app.cget('menu'))
        file_menu = next(self.app.nametowidget(menu.entrycget(i, 'menu')) for i in range(menu.index('end') + 1)
                         if menu.type(i) == 'cascade' and menu.entrycget(i, 'label') == 'Arquivo')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'book.xlsx'; write_book(path)
            with patch('app.filedialog.askopenfilename', return_value=str(path)), patch('app.read_excel_workbook', side_effect=worker_read):
                file_menu.invoke('Abrir Excel…')
                self.assertIsNotNone(self.app._task_window)
                self.assertEqual(menu.entrycget('Arquivo', 'state'), 'disabled')
                drain_task(self.app)
        self.assertNotEqual(threads, [threading.get_ident()])
        self.assertEqual(len(threads), 1)
        self.assertEqual(self.app.rows, [['Valor', ''], ['5', '10']])
        self.assertEqual(len(self.app.document['worksheets']), 3)
        self.assertEqual(menu.entrycget('Arquivo', 'state'), 'normal')

    def test_excel_cancel_discards_ready_project_before_replace_confirmation(self):
        before = deepcopy(self.app.document)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'book.xlsx'; write_book(path)
            self.assertTrue(self.app.start_excel_import(path))
            self.app._task_window.task.thread.join(3.)
            self.app._task_window.cancel()
            with patch.object(self.app, 'confirm_replace', side_effect=AssertionError('must not replace')):
                drain_task(self.app)
        self.assertEqual(self.app.document, before)

    def test_excel_failure_is_reported_on_tk_thread_without_replacing_work(self):
        before = deepcopy(self.app.document); threads = []
        def show_error(*args, **kwargs): threads.append(threading.get_ident())
        with patch('app.read_excel_workbook', side_effect=ValueError('invalid workbook')):
            self.assertTrue(self.app.start_excel_import('invalid.xlsx'))
            with patch('task_dialog.messagebox.showerror', side_effect=show_error): drain_task(self.app)
        self.assertEqual(threads, [threading.get_ident()])
        self.assertEqual(self.app.document, before)

    def test_excel_generation_undo_save_reopen_and_export(self):
        from project import load_document
        from analysis_service import rerun_analysis
        import json
        self.app.dirty = False
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'book.xlsx'; write_book(path)
            self.assertTrue(self.app.start_excel_import(path)); drain_task(self.app)
            self.assertTrue(self.random()); drain_task(self.app)
            record = deepcopy(self.app.document['analyses'][-1])
            self.assertTrue(self.app.run_ttest('one', 2))
            self.app.undo_data(); self.assertEqual(len(self.app.headers), 2)
            self.app.redo_data(); self.assertEqual(len(self.app.headers), 4)
            saved = Path(directory) / 'result.statlab'; self.app.project_path = str(saved)
            self.assertTrue(self.app.save_project())
            document = load_document(saved)
            self.assertEqual(rerun_analysis(document, record['analysis_id'])['values'], record['values'])
            self.assertEqual(rerun_analysis(document, document['analyses'][-1]['analysis_id'])['values'], document['analyses'][-1]['values'])
            history = self.app.analysis_history_dialog()
            history.tree.selection_set(record['analysis_id']); history.show()
            output = Path(directory) / 'result.json'
            with patch('analysis_history_dialog.filedialog.asksaveasfilename', return_value=str(output)):history.export()
            self.assertEqual(json.loads(output.read_text(encoding='utf-8'))['values'], record['values'])
            history.destroy()

    def test_excel_changed_project_and_declined_confirmation_preserve_work(self):
        for edit in ('none', 'data', 'metadata'):
            with self.subTest(edit=edit), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / 'book.xlsx'; write_book(path)
                self.assertTrue(self.app.start_excel_import(path))
                self.app._task_window.task.thread.join(3.)
                if edit == 'data':
                    self.app.rows[0][0] = 'edited'; self.app.data_changed()
                elif edit == 'metadata':
                    active_sheet(self.app.document)['columns'][0]['format']['decimals'] = 3
                self.app.sync_document(); before = deepcopy(self.app.document)
                with patch.object(self.app, 'confirm_replace', return_value=False) as confirm, patch('task_dialog.messagebox.showerror') as error:
                    drain_task(self.app)
                self.assertEqual(self.app.document, before)
                if edit != 'none': error.assert_called_once(); confirm.assert_not_called()
                else: confirm.assert_called_once(); error.assert_not_called()

    def test_close_requests_cancellation_before_existing_save_prompt(self):
        started = threading.Event()
        def work(context):
            started.set()
            while True:
                context.cancelled.wait(.005); context.checkpoint()
        applied = []
        self.app.start_background_task('Teste', work, applied.append)
        self.assertTrue(started.wait(2.))
        before = deepcopy(self.app.document)
        with patch.object(self.app, 'confirm_replace', return_value=False) as confirm:
            self.app.close(); drain_task(self.app)
        confirm.assert_called_once()
        self.assertEqual(applied, [])
        self.assertEqual(self.app.document, before)

    def test_destroy_cancels_worker_and_removes_tk_poll_callback(self):
        started = threading.Event()
        def work(context):
            started.set()
            while True:
                context.cancelled.wait(.005); context.checkpoint()
        self.app.start_background_task('Teste', work, lambda value: self.fail('must not apply'))
        self.assertTrue(started.wait(2.))
        task = self.app._task_window.task
        self.app.destroy(); self.app = None
        task.thread.join(2.)
        self.assertFalse(task.thread.is_alive())
        self.assertEqual(self.callback_errors, [])
