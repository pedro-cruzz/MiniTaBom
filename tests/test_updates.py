import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

import updates
from app import MiniTaBom


class UpdateTests(unittest.TestCase):
    def release(self, tag='v0.2.0', **options):
        return io.BytesIO(json.dumps(dict(tag_name=tag, draft=False, prerelease=False, **options)).encode())

    def test_repository_normalization_and_reject_other_hosts_or_paths(self):
        self.assertEqual(updates.normalize_repository(' https://github.com/test/MiniTaBom.git/ '), 'test/MiniTaBom')
        for value in ['', 'http://github.com/test/app', 'https://github.com.evil.test/a/b',
                      'https://github.com/test/app?x=1', 'https://github.com/test/app/releases',
                      'test/..', 'https://user@github.com/test/app', 'test/app#fragment']:
            with self.subTest(value=value), self.assertRaises(ValueError):
                updates.normalize_repository(value)

    def test_semantic_version_order_and_build_metadata(self):
        versions = ['0.1.0', '0.2.0-alpha', '0.2.0-alpha.2', '0.2.0-alpha.10',
                    '0.2.0-beta', '0.2.0-rc.1', '0.2.0', '0.9.0', '0.10.0', '1.0.0']
        self.assertEqual(sorted(versions, key=updates.version_key), versions)
        self.assertEqual(updates.version_key('v1.2.3+build.5'), updates.version_key('1.2.3'))
        for value in ['latest', '1.2', '01.2.3', '1.2.3-01']:
            with self.assertRaises(ValueError):
                updates.version_key(value)

    def test_new_release_uses_bounded_request_and_constructed_github_url(self):
        with patch('updates.urlopen', return_value=self.release(html_url='https://bad.test/')) as request:
            result = updates.check_latest('test/MiniTaBom', '0.1.0')
        self.assertTrue(result['newer'])
        self.assertEqual(result['url'], 'https://github.com/test/MiniTaBom/releases/tag/v0.2.0')
        self.assertEqual(request.call_args.kwargs['timeout'], 10)
        self.assertEqual(request.call_args.args[0].full_url,
                         'https://api.github.com/repos/test/MiniTaBom/releases/latest')
        self.assertNotIn('Authorization', request.call_args.args[0].headers)

    def test_equal_and_older_release_do_not_offer_upgrade(self):
        for tag in ['v0.1.0', 'v0.0.9']:
            with patch('updates.urlopen', return_value=self.release(tag)):
                self.assertFalse(updates.check_latest('test/app', '0.1.0')['newer'])

    def test_network_errors_are_explained_without_claiming_up_to_date(self):
        for error, message in [(URLError('offline'), 'internet'), (TimeoutError(), 'internet'),
                               (HTTPError('url', 404, 'Not Found', {}, None), 'Release estável'),
                               (HTTPError('url', 403, 'Forbidden', {}, None), 'limitou'),
                               (HTTPError('url', 500, 'Server error', {}, None), 'HTTP 500')]:
            with patch('updates.urlopen', side_effect=error), self.assertRaisesRegex(ValueError, message):
                updates.check_latest('test/app', '0.1.0')

    def test_invalid_or_oversized_release_response(self):
        payloads = [b'bad json', b'[]', b'{}', b'x' * (512 * 1024 + 1),
                    json.dumps(dict(tag_name='v1.0.0', prerelease=True)).encode(),
                    json.dumps(dict(tag_name='v1.0.0', draft=True)).encode(),
                    json.dumps(dict(tag_name='latest')).encode()]
        for payload in payloads:
            with patch('updates.urlopen', return_value=io.BytesIO(payload)), self.assertRaises(ValueError):
                updates.check_latest('test/app', '0.1.0')

    def test_repository_preferences_persist_outside_project(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'MiniTaBom' / 'updates.json'
            with patch('updates.preferences_path', return_value=path), patch('updates.load_metadata', return_value={'repository': 'owner/default'}):
                self.assertEqual(updates.configured_repository(), 'owner/default')
                updates.save_repository('https://github.com/owner/choice')
                self.assertEqual(updates.configured_repository(), 'owner/choice')
                self.assertEqual(json.loads(path.read_text(encoding='utf-8')), {'repository': 'owner/choice'})


class UpdateInterfaceTests(unittest.TestCase):
    def setUp(self):
        self.app = MiniTaBom()
        self.app.withdraw()
        self.addCleanup(self.app.destroy)
        self.repo_patch = patch('update_dialog.configured_repository', return_value='test/app')
        self.repo_patch.start()
        self.addCleanup(self.repo_patch.stop)

    def test_help_menu_and_single_dialog(self):
        menu = self.app.nametowidget(self.app.cget('menu'))
        help_menu = self.app.nametowidget(menu.entrycget('Ajuda', 'menu'))
        self.assertTrue(help_menu.entrycget('Verificar atualizações…', 'image'))
        dialog = self.app.update_dialog()
        self.assertIs(self.app.update_dialog(), dialog)
        self.assertEqual(dialog.current_version, updates.load_metadata()['version'])
        dialog.destroy()

    def test_check_disables_duplicate_requests_and_enables_release_link(self):
        dialog = self.app.update_dialog()
        with patch('update_dialog.threading.Thread') as thread, patch('update_dialog.save_repository'):
            dialog.check()
            dialog.check()
        thread.assert_called_once()
        self.assertEqual(str(dialog.check_button.cget('state')), 'disabled')
        dialog.after_cancel(dialog.poll_id)
        dialog.poll_id = None
        dialog.results.put((True, dict(latest='v0.2.0', newer=True,
                                      url='https://github.com/test/app/releases/tag/v0.2.0')))
        dialog.poll()
        self.assertIn('Nova versão', dialog.message.cget('text'))
        self.assertEqual(str(dialog.open_button.cget('state')), 'normal')
        with patch('update_dialog.webbrowser.open', return_value=True) as browser:
            dialog.open_button.invoke()
        browser.assert_called_once_with('https://github.com/test/app/releases/tag/v0.2.0')
        dialog.destroy()

    def test_failure_and_invalid_repository_do_not_open_browser(self):
        dialog = self.app.update_dialog()
        dialog.repository.delete(0, 'end')
        dialog.repository.insert(0, 'invalid')
        with patch('update_dialog.threading.Thread') as thread:
            dialog.check()
        thread.assert_not_called()
        dialog.results.put((False, 'Sem internet'))
        dialog.poll()
        self.assertEqual(dialog.message.cget('text'), 'Sem internet')
        self.assertEqual(str(dialog.open_button.cget('state')), 'disabled')
        dialog.destroy()

    def test_closing_dialog_cancels_pending_ui_callback(self):
        dialog = self.app.update_dialog()
        with patch('update_dialog.threading.Thread'), patch('update_dialog.save_repository'):
            dialog.check()
        callback = dialog.poll_id
        dialog.destroy()
        self.assertNotIn(callback, self.app.tk.call('after', 'info'))
        # Uma resposta tardia só escreve na fila Python; não acessa Tk destruído.
        with patch('update_dialog.check_latest', return_value=dict(newer=False)):
            dialog.worker('test/app')
        self.assertEqual(dialog.results.get_nowait(), (True, dict(newer=False)))


if __name__ == '__main__':
    unittest.main()
