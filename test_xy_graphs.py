import math
import unittest
import xml.etree.ElementTree as ET

from xy_graphs import prepare_xy, xy_scene, scene_svg


class XYGraphTests(unittest.TestCase):
    def test_pairs_groups_row_numbers_and_input_snapshot(self):
        rows = [['1', '2', 'B'], ['2', '3', 'A'], ['*', '4', 'B'], ['4', '', 'A'], ['5', '6', '*']]
        r = prepare_xy(['X', 'Y', 'G'], rows, 1, 0, group=2)
        self.assertEqual((r['n'], r['missing']), (2, 3))
        self.assertEqual([s['label'] for s in r['series']], ['B', 'A'])
        self.assertEqual(r['series'][1]['points'], [dict(x=2., y=3., row=2)])
        rows[0][0] = '999'
        self.assertEqual(r['series'][0]['points'][0]['x'], 1)

    def test_time_gaps_and_explicit_connection(self):
        rows = [['2'], ['*'], ['4'], ['6']]
        r = prepare_xy(['Y'], rows, 0, kind='time')
        series = r['series'][0]
        self.assertEqual([p['x'] for p in series['points']], [1, 3, 4])
        self.assertEqual([[p['row'] for p in s] for s in series['segments']], [[1], [3, 4]])
        scene = xy_scene(r)
        self.assertEqual(sum(i.get('role') == 'series' for i in scene['items']), 1)
        r = prepare_xy(['Y'], rows, 0, kind='time', connect_missing=True)
        self.assertEqual(len(r['series'][0]['segments']), 1)

    def test_time_axis_uses_integer_row_ticks(self):
        model = prepare_xy(['Y'], [[str(v)] for v in range(10)], 0, kind='time')
        labels = [item['text'] for item in xy_scene(model, 940, 540)['items']
                  if item['kind'] == 'text' and item['y'] == 486]
        self.assertEqual(labels, ['2', '4', '6', '8', '10'])

    def test_interleaved_groups_preserve_order_and_missing_group_breaks_all(self):
        rows = [['1', 'B'], ['2', 'A'], ['3', 'B'], ['4', '*'], ['5', 'B'], ['6', 'A']]
        r = prepare_xy(['Y', 'G'], rows, 0, group=1, kind='time')
        self.assertEqual([[p['row'] for p in s] for s in r['series'][0]['segments']], [[1, 3], [5]])
        self.assertEqual([[p['row'] for p in s] for s in r['series'][1]['segments']], [[2], [6]])

    def test_scatter_lines_are_never_implicitly_sorted_or_averaged(self):
        rows = [['3', '4'], ['1', '2'], ['1', '5']]
        r = prepare_xy(['X', 'Y'], rows, 1, 0, connect=True)
        self.assertEqual([p['x'] for p in r['series'][0]['points']], [3, 1, 1])
        self.assertEqual(r['n'], 3)

    def test_logarithmic_scale_has_equal_decade_spacing(self):
        r = prepare_xy(['X', 'Y'], [['1', '1'], ['10', '10'], ['100', '100']], 1, 0, x_log=True, y_log=True)
        points = [i for i in xy_scene(r)['items'] if i['kind'] == 'circle']
        self.assertAlmostEqual(points[1]['x'] - points[0]['x'], points[2]['x'] - points[1]['x'])
        self.assertAlmostEqual(points[0]['y'] - points[1]['y'], points[1]['y'] - points[2]['y'])
        with self.assertRaisesRegex(ValueError, 'maiores que zero'):
            prepare_xy(['X', 'Y'], [['0', '2']], 1, 0, x_log=True)

    def test_extreme_constant_and_small_values_keep_finite_coordinates(self):
        for values in ([1e308, -1e308], [5e-324, 1e-323], [2., 2.], [0., 0.]):
            model = prepare_xy(['Y'], [[str(v)] for v in values], 0, kind='time')
            for item in xy_scene(model)['items']:
                coords = item['coords'] if item['kind'] == 'line' else [item['x'], item['y']]
                self.assertTrue(all(math.isfinite(v) for v in coords))

    def test_svg_is_standalone_xml_with_escaped_text_and_point_details(self):
        model = prepare_xy(['Y'], [['1'], ['3']], 0, kind='time', title='A < B & "C"', y_label='Medição')
        svg = scene_svg(xy_scene(model))
        root = ET.fromstring(svg)
        ns = {'s': 'http://www.w3.org/2000/svg'}
        self.assertEqual(root.attrib['role'], 'img')
        self.assertEqual(len(root.findall('s:circle', ns)), 2)
        texts = [e.text for e in root.findall('s:text', ns)]
        self.assertIn('A < B & "C"', texts)
        self.assertIn('Medição', texts)
        self.assertTrue(all(c.find('s:title', ns).text.startswith('Linha ') for c in root.findall('s:circle', ns)))

    def test_invalid_selection_data_and_limits_are_rejected(self):
        for args in [dict(y=-1), dict(y=True), dict(y=0, x=None), dict(y=1, x=0, group=1), dict(y=1, x=0, kind='bad')]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                prepare_xy(['X', 'Y'], [['1', '2']], **args)
        for rows in ([['*', '2']], [['1', 'nan']], [['bad', '*']]):
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                prepare_xy(['X', 'Y'], rows, 1, 0)
        with self.assertRaisesRegex(ValueError, '20 grupos'):
            prepare_xy(['Y', 'G'], [[str(i), str(i)] for i in range(21)], 0, group=1, kind='time')


if __name__ == '__main__':
    unittest.main()
