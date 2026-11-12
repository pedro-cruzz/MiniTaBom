import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.build_windows import install_bundle, finish_bundle


class BundleInstallTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.bundle = self.root / 'bundle'
        self.bundle.mkdir()
        (self.bundle / 'MiniTaBom.exe').write_bytes(b'new executable')
        (self.bundle / 'versao.json').write_text('{"version":"0.9.0"}', encoding='utf-8')
        self.application = self.root / 'Aplicativo'
        self.application.mkdir()
        (self.application / 'MiniTaBom.exe').write_bytes(b'old executable in use')
        (self.application / 'estudo.statlab').write_text('personal data', encoding='utf-8')

    def test_versioned_install_preserves_old_executable_and_personal_data(self):
        installed = install_bundle(self.bundle, self.application, '0.9.0', 'build1')
        self.assertEqual((installed / 'MiniTaBom.exe').read_bytes(), b'new executable')
        self.assertEqual((self.application / 'MiniTaBom.exe').read_bytes(), b'old executable in use')
        self.assertEqual((self.application / 'estudo.statlab').read_text(encoding='utf-8'), 'personal data')
        selected = json.loads((self.application / 'atual.json').read_text(encoding='utf-8'))
        self.assertEqual(self.application / selected['executable'], installed / 'MiniTaBom.exe')
        self.assertIn(str((installed / 'MiniTaBom.exe').relative_to(self.application)), (self.application / 'Abrir.bat').read_text(encoding='ascii'))
        second = install_bundle(self.bundle, self.application, '0.9.0', 'build2')
        self.assertTrue((installed / 'MiniTaBom.exe').exists())
        self.assertNotEqual(second, installed)

    def test_failed_copy_does_not_change_current_launcher_or_selection(self):
        install_bundle(self.bundle, self.application, '0.9.0', 'build1')
        original = {name: (self.application / name).read_bytes() for name in ['atual.json', 'Abrir.bat']}
        with patch('tools.build_windows.shutil.copytree', side_effect=OSError('disk full')), self.assertRaises(OSError):
            install_bundle(self.bundle, self.application, '0.9.0', 'build2')
        for name, contents in original.items(): self.assertEqual((self.application / name).read_bytes(), contents)

    def test_reused_or_external_destination_is_rejected(self):
        install_bundle(self.bundle, self.application, '0.9.0', 'build1')
        with self.assertRaises(ValueError): install_bundle(self.bundle, self.application, '0.9.0', 'build1')
        with self.assertRaises(ValueError): install_bundle(self.bundle, self.application, '../outside', 'build2')
        with self.assertRaises(ValueError): install_bundle(self.bundle, self.application, '0.9.0', '../../../outside')

    def test_unapproved_frozen_bundle_cannot_be_published(self):
        build = self.root / 'build'
        build.mkdir()
        for report in [dict(ok=False, frozen=True), dict(ok=True, frozen=False)]:
            (build / 'smoke-test.json').write_text(json.dumps(report), encoding='utf-8')
            with self.assertRaises(ValueError): finish_bundle(self.bundle, build, dict(version='0.9.0'))
        self.assertFalse((self.application / 'atual.json').exists())
