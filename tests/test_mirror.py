"""Tests for SwayDeck wl-mirror lifecycle management."""

import pathlib
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, call, patch

SRC = pathlib.Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from swaydeck import (
    MirrorError,
    mirror_alive,
    require_wl_mirror,
    start_mirror,
    stop_mirror,
)


class MirrorAliveTests(unittest.TestCase):
    def test_missing_pid_file_is_not_alive(self):
        with tempfile.TemporaryDirectory() as tmp:
            pid_file = pathlib.Path(tmp) / "mirror.pids"

            self.assertFalse(
                mirror_alive(pid_file)
            )

    @patch("swaydeck.mirror._pid_is_wl_mirror")
    def test_any_verified_pid_counts_as_alive(
        self,
        verify,
    ):
        verify.side_effect = [
            False,
            True,
        ]

        with tempfile.TemporaryDirectory() as tmp:
            pid_file = pathlib.Path(tmp) / "mirror.pids"
            pid_file.write_text(
                "101\n"
                "not-a-pid\n"
                "202\n"
            )

            self.assertTrue(
                mirror_alive(pid_file)
            )

        self.assertEqual(
            verify.call_args_list,
            [
                call(101),
                call(202),
            ],
        )


class StopMirrorTests(unittest.TestCase):
    @patch("swaydeck.mirror.os.kill")
    @patch("swaydeck.mirror._pid_is_wl_mirror")
    def test_only_verified_mirror_pids_are_terminated(
        self,
        verify,
        kill,
    ):
        verify.side_effect = [
            True,
            False,
        ]

        with tempfile.TemporaryDirectory() as tmp:
            pid_file = pathlib.Path(tmp) / "mirror.pids"
            pid_file.write_text(
                "101\n202\n"
            )

            stop_mirror(
                pid_file
            )

            self.assertFalse(
                pid_file.exists()
            )

        kill.assert_called_once_with(
            101,
            __import__("signal").SIGTERM,
        )


class StartMirrorTests(unittest.TestCase):
    def test_requires_external_output(self):
        with self.assertRaisesRegex(
            MirrorError,
            "no external outputs",
        ):
            start_mirror(
                "eDP-1",
                [],
            )

    @patch(
        "swaydeck.mirror.shutil.which",
        return_value=None,
    )
    def test_missing_binary_is_reported(
        self,
        which,
    ):
        with self.assertRaisesRegex(
            MirrorError,
            "not installed",
        ):
            start_mirror(
                "eDP-1",
                ["HDMI-A-1"],
            )

        which.assert_called_once_with(
            "wl-mirror"
        )

    @patch("swaydeck.mirror.time.sleep")
    @patch(
        "swaydeck.mirror.mirror_alive",
        return_value=True,
    )
    @patch("swaydeck.mirror.stop_mirror")
    @patch(
        "swaydeck.mirror.shutil.which",
        return_value="/usr/bin/wl-mirror",
    )
    @patch("swaydeck.mirror.subprocess.Popen")
    def test_starts_one_process_per_external(
        self,
        popen,
        which,
        stop,
        alive,
        sleep,
    ):
        first = MagicMock()
        first.pid = 101

        second = MagicMock()
        second.pid = 202

        popen.side_effect = [
            first,
            second,
        ]

        with tempfile.TemporaryDirectory() as tmp:
            pid_file = pathlib.Path(tmp) / "mirror.pids"

            pids = start_mirror(
                "eDP-1",
                [
                    "HDMI-A-1",
                    "DP-1",
                ],
                pid_file=pid_file,
            )

            self.assertEqual(
                pids,
                (101, 202),
            )

            self.assertEqual(
                pid_file.read_text(),
                "101\n202\n",
            )

            stop.assert_called_once_with(
                pid_file
            )

            alive.assert_called_once_with(
                pid_file
            )

        self.assertEqual(
            popen.call_count,
            2,
        )

        self.assertEqual(
            popen.call_args_list[0].args[0],
            [
                "/usr/bin/wl-mirror",
                "--fullscreen-output",
                "HDMI-A-1",
                "--fullscreen",
                "eDP-1",
            ],
        )

        self.assertEqual(
            popen.call_args_list[1].args[0],
            [
                "/usr/bin/wl-mirror",
                "--fullscreen-output",
                "DP-1",
                "--fullscreen",
                "eDP-1",
            ],
        )

        sleep.assert_called_once_with(
            0.2
        )

    @patch("swaydeck.mirror.time.sleep")
    @patch(
        "swaydeck.mirror.mirror_alive",
        return_value=False,
    )
    @patch("swaydeck.mirror.stop_mirror")
    @patch(
        "swaydeck.mirror.shutil.which",
        return_value="/usr/bin/wl-mirror",
    )
    @patch("swaydeck.mirror.subprocess.Popen")
    def test_failed_verification_cleans_up(
        self,
        popen,
        which,
        stop,
        alive,
        sleep,
    ):
        process = MagicMock()
        process.pid = 101
        process.poll.return_value = None

        popen.return_value = process

        with tempfile.TemporaryDirectory() as tmp:
            pid_file = pathlib.Path(tmp) / "mirror.pids"

            with self.assertRaisesRegex(
                MirrorError,
                "failed to remain running",
            ):
                start_mirror(
                    "eDP-1",
                    ["HDMI-A-1"],
                    pid_file=pid_file,
                )

            self.assertFalse(
                pid_file.exists()
            )

        process.terminate.assert_called_once_with()

    def test_negative_verification_delay_is_rejected(self):
        with self.assertRaisesRegex(
            ValueError,
            "must not be negative",
        ):
            start_mirror(
                "eDP-1",
                ["HDMI-A-1"],
                verify_delay=-1,
            )


class RequireMirrorTests(unittest.TestCase):
    @patch(
        "swaydeck.mirror.shutil.which",
        return_value="/usr/bin/wl-mirror",
    )
    def test_available_binary_is_returned(
        self,
        which,
    ):
        self.assertEqual(
            require_wl_mirror(),
            "/usr/bin/wl-mirror",
        )

        which.assert_called_once_with(
            "wl-mirror"
        )

    @patch(
        "swaydeck.mirror.shutil.which",
        return_value=None,
    )
    def test_missing_binary_is_rejected(
        self,
        which,
    ):
        with self.assertRaisesRegex(
            MirrorError,
            "not installed",
        ):
            require_wl_mirror()


if __name__ == "__main__":
    unittest.main()
