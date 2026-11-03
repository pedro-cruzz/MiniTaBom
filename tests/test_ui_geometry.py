import unittest

from ui_geometry import centered_position


class GeometryTests(unittest.TestCase):
    def test_secondary_monitor_to_the_right(self):
        self.assertEqual(centered_position((2500, 100, 1180, 790), (980, 640), (1920, 0, 3840, 1040)), (2600, 175))

    def test_negative_monitor_coordinates(self):
        self.assertEqual(centered_position((-1600, 100, 1180, 790), (980, 640), (-1920, 0, 0, 1040)), (-1500, 175))

    def test_clamps_to_work_area_without_taskbar_overlap(self):
        self.assertEqual(centered_position((3700, 900, 1180, 790), (980, 640), (1920, 0, 3840, 1040)), (2852, 360))

    def test_fallback_keeps_parent_monitor_and_oversized_window_anchors_at_start(self):
        self.assertEqual(centered_position((2500, 100, 1180, 790), (980, 640)), (2600, 175))
        self.assertEqual(centered_position((0, 0, 1180, 790), (2000, 1200), (0, 0, 1920, 1040)), (8, 8))
