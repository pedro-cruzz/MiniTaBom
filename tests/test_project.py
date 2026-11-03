import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

from project import load_project, save_project, validate_project
from app import MiniTaBom


class ProjectTests(unittest.TestCase):
    def test_round_trip_preserves_text_missing_and_results(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'medição.statlab'
            headers = ['Medição', 'Grupo']
            rows = [['1,5', 'ação'], ['*', ''], ['', 'B']]
            output = 'Média: 1,5\nObservações: ação\n'
            save_project(path, headers, rows, output)
            self.assertEqual(load_project(path), (headers, rows, output))

    def test_invalid_project_is_rejected(self):
        valid = dict(format='statlab', version=1, headers=['A'], rows=[['1']], output='')
        for override in [dict(version=2), dict(version=True), dict(format='mpj'),
                dict(headers=[]), dict(headers=['A', 'A']), dict(headers=[' ']),
                dict(rows=[[]]), dict(rows=[[1]]), dict(output=None)]:
            with self.subTest(override=override), self.assertRaises(ValueError):
                validate_project(dict(valid, **override))
        with self.assertRaises(ValueError):
            validate_project([])

    def test_bad_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'bad.statlab'
            for content in [b'{', b'\xff', json.dumps({}).encode()]:
                path.write_bytes(content)
                with self.assertRaises(ValueError):
                    load_project(path)

    def test_failed_replace_preserves_existing_file_and_cleans_temp(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'sample.statlab'
            save_project(path, ['A'], [['original']], 'resultado original')
            before = path.read_bytes()
            with patch('project.os.replace', side_effect=OSError('Falha simulada')):
                with self.assertRaises(OSError):
                    save_project(path, ['A'], [['novo']], 'novo resultado')
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(list(Path(directory).iterdir()), [path])

    def test_save_cancel_and_failure_prevent_replacement(self):
        for answer, saved, expected in [(None, True, False), (False, False, True),
                (True, False, False), (True, True, True)]:
            model = SimpleNamespace(dirty=True, save_project=lambda: saved)
            with self.subTest(answer=answer, saved=saved):
                with patch('app.messagebox.askyesnocancel', return_value=answer):
                    self.assertEqual(MiniTaBom.confirm_replace(model), expected)


if __name__ == '__main__':
    unittest.main()
