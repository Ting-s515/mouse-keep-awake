import os
import select
import unittest
from unittest.mock import patch

from Xlib import X, display

from mouse_backend import create_backend
from mouse_backend.linux_x11 import LinuxX11Backend


class LinuxX11BackendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not os.environ.get("DISPLAY"):
            raise unittest.SkipTest("X11 整合測試需要 DISPLAY，請由 Xvfb 測試映像啟動")

    def setUp(self):
        self.observer = display.Display()
        self.root = self.observer.screen().root
        self.root.change_attributes(event_mask=X.PointerMotionMask)
        self.observer.sync()

    def tearDown(self):
        self.observer.close()

    def _clear_motion_events(self):
        while self.observer.pending_events():
            self.observer.next_event()

    def _wait_for_motion(self):
        ready, _, _ = select.select([self.observer.fileno()], [], [], 2)
        self.assertTrue(ready, "X11 server 未送出 PointerMotion event")
        event = self.observer.next_event()
        self.assertEqual(event.type, X.MotionNotify)
        return event

    def _warp_pointer(self, x, y):
        self.root.warp_pointer(x, y)
        self.observer.sync()
        self._clear_motion_events()

    def test_backend_selection_and_origin_reset_send_motion_event(self):
        with patch.dict(os.environ, {"WAYLAND_DISPLAY": ""}):
            backend = create_backend()
        self.assertIsInstance(backend, LinuxX11Backend)

        try:
            self._warp_pointer(100, 100)
            backend.move_to_origin()
            event = self._wait_for_motion()
            self.assertEqual((event.root_x, event.root_y), (0, 0))
            pointer = self.root.query_pointer()
            self.assertEqual((pointer.root_x, pointer.root_y), (0, 0))
        finally:
            backend.close()

    def test_relative_moves_emit_events_in_all_four_quadrants(self):
        backend = LinuxX11Backend()
        center = (400, 300)
        directions = ((-5, -5), (5, -5), (-5, 5), (5, 5))

        try:
            for dx, dy in directions:
                with self.subTest(dx=dx, dy=dy):
                    self._warp_pointer(*center)
                    backend.move_relative(dx, dy)
                    event = self._wait_for_motion()
                    expected = (center[0] + dx, center[1] + dy)
                    self.assertEqual((event.root_x, event.root_y), expected)
                    pointer = self.root.query_pointer()
                    self.assertEqual((pointer.root_x, pointer.root_y), expected)
        finally:
            backend.close()


if __name__ == "__main__":
    unittest.main()
