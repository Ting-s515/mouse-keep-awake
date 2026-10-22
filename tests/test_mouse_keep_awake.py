import sys
import unittest
from unittest.mock import patch

import mouse_keep_awake


class FakeBackend:
    name = "fake"

    def __init__(self):
        self.events = []

    def move_to_origin(self):
        self.events.append(("origin",))

    def move_relative(self, dx, dy):
        self.events.append((dx, dy))

    def close(self):
        return None


class StopLoop(Exception):
    pass


class MouseKeepAwakeTests(unittest.TestCase):
    def test_run_resets_immediately_then_moves_in_each_allowed_direction(self):
        backend = FakeBackend()
        sleep_calls = []

        def stop_after_all_directions(interval_seconds):
            sleep_calls.append(interval_seconds)
            if len(sleep_calls) > len(mouse_keep_awake.MOVEMENTS):
                raise StopLoop

        with (
            patch("mouse_keep_awake.time.sleep", side_effect=stop_after_all_directions),
            patch(
                "mouse_keep_awake.random.choice",
                side_effect=mouse_keep_awake.MOVEMENTS,
            ),
            self.assertLogs("mouse_keep_awake", level="INFO") as captured,
        ):
            with self.assertRaises(StopLoop):
                mouse_keep_awake.run(backend, interval_seconds=17)

        self.assertEqual(backend.events, [("origin",), *mouse_keep_awake.MOVEMENTS])
        self.assertEqual(sleep_calls, [17] * 5)
        self.assertEqual(
            sum("下次移動時間" in message for message in captured.output),
            len(mouse_keep_awake.MOVEMENTS) + 1,
        )
        for direction in mouse_keep_awake.DIRECTION_NAMES.values():
            self.assertTrue(any(direction in message for message in captured.output))

    def test_main_rejects_non_positive_interval_before_backend_initialization(self):
        with (
            patch.object(sys, "argv", ["mouse_keep_awake.py", "--interval-seconds", "0"]),
            patch("mouse_keep_awake.create_backend") as create_backend,
            self.assertRaises(SystemExit) as raised,
        ):
            mouse_keep_awake.main()

        self.assertEqual(raised.exception.code, 2)
        create_backend.assert_not_called()


if __name__ == "__main__":
    unittest.main()
