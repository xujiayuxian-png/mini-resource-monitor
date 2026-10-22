import importlib.util
from pathlib import Path
import re
import subprocess
import unittest
from unittest.mock import patch

import gi

gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gtk


spec = importlib.util.spec_from_file_location(
    'monitor', Path(__file__).resolve().parents[1] / 'src' / 'monitor.py')
monitor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(monitor)


def settle():
    loop = GLib.MainLoop()
    GLib.timeout_add(250, lambda: (loop.quit(), False)[1])
    loop.run()


class WindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.window = monitor.Monitor()
        settle()

    @classmethod
    def tearDownClass(cls):
        cls.window.disconnect_by_func(Gtk.main_quit)
        cls.window.destroy()

    def test_shape_covers_device_pixel_window(self):
        window = self.window
        result = subprocess.check_output(
            ['xwininfo', '-shape', '-id', str(window.get_window().get_xid())],
            text=True)
        size = re.search(r'Window shape extents:.*?(\d+)x(\d+)', result)
        self.assertIsNotNone(size, result)
        scale = window.get_scale_factor()
        self.assertEqual(tuple(map(int, size.groups())),
                         (window.get_allocated_width() * scale,
                          window.get_allocated_height() * scale))

    def test_in_bounds_window_does_not_schedule_another_move(self):
        with patch.object(self.window, 'move') as move:
            self.window.keep_in_workarea()
            move.assert_not_called()

    def test_configure_events_settle(self):
        events = []
        handler = self.window.connect('configure-event',
                                      lambda *_: events.append(True) or False)
        settle()
        self.window.disconnect(handler)
        self.assertLess(len(events), 5)

    def test_pinning_preserves_window_identity(self):
        window = self.window
        xid = window.get_window().get_xid()
        for pinned in (True, False):
            window.pin.set_active(pinned)
            settle()
            self.assertEqual(window.get_window().get_xid(), xid)
            properties = subprocess.check_output(
                ['xprop', '-id', str(xid), '_NET_WM_STATE',
                 'WM_TRANSIENT_FOR'], text=True)
            self.assertEqual('_NET_WM_STATE_ABOVE' in properties, pinned)
            self.assertIn('WM_TRANSIENT_FOR:  not found.', properties)


if __name__ == '__main__':
    unittest.main()
