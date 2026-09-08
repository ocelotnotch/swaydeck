"""Tests for SwayDeck's display mutation command layer."""

import pathlib
import subprocess
import sys
import unittest
from unittest.mock import patch

SRC = pathlib.Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from swaydeck import (
    SwayCommandError,
    disable_output,
    enable_output,
    position_output,
    run_sway_command,
    scale_output,
    transform_output,
)


class SwayCommandTests(unittest.TestCase):
    @patch("swaydeck.sway.subprocess.run")
    def test_enable_output(self, run):
        run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="",
            stderr="",
        )

        enable_output("eDP-1")

        run.assert_called_once_with(
            [
                "swaymsg",
                "-q",
                "--",
                "output eDP-1 enable",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=5.0,
        )

    @patch("swaydeck.sway.subprocess.run")
    def test_disable_output(self, run):
        run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="",
            stderr="",
        )

        disable_output("HDMI-A-1")

        self.assertIn(
            "output HDMI-A-1 disable",
            run.call_args.args[0],
        )

    @patch("swaydeck.sway.subprocess.run")
    def test_position_output(self, run):
        run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="",
            stderr="",
        )

        position_output(
            "HDMI-A-1",
            1920,
            -120,
        )

        self.assertIn(
            "output HDMI-A-1 position 1920 -120",
            run.call_args.args[0],
        )

    @patch("swaydeck.sway.subprocess.run")
    def test_scale_output(self, run):
        run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="",
            stderr="",
        )

        scale_output(
            "eDP-1",
            1.5,
        )

        self.assertIn(
            "output eDP-1 scale 1.5",
            run.call_args.args[0],
        )

    @patch("swaydeck.sway.subprocess.run")
    def test_transform_output(self, run):
        run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="",
            stderr="",
        )

        transform_output(
            "HDMI-A-1",
            "90",
        )

        self.assertIn(
            "output HDMI-A-1 transform 90",
            run.call_args.args[0],
        )

    def test_scale_must_be_positive(self):
        with self.assertRaisesRegex(
            ValueError,
            "greater than zero",
        ):
            scale_output(
                "eDP-1",
                0,
            )

    def test_transform_is_validated(self):
        with self.assertRaisesRegex(
            ValueError,
            "unsupported transform",
        ):
            transform_output(
                "eDP-1",
                "banana",
            )

    def test_empty_command_is_rejected(self):
        with self.assertRaisesRegex(
            ValueError,
            "must not be empty",
        ):
            run_sway_command("   ")

    @patch("swaydeck.sway.subprocess.run")
    def test_sway_failure_is_propagated(self, run):
        run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout="",
            stderr="Error: Invalid output command",
        )

        with self.assertRaisesRegex(
            SwayCommandError,
            "Invalid output command",
        ):
            enable_output("eDP-1")


if __name__ == "__main__":
    unittest.main()
