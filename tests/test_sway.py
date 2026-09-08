"""Tests for the read-only Sway adapter."""

import pathlib
import subprocess
import sys
import unittest
from unittest.mock import patch

SRC = pathlib.Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from swaydeck import (
    Rect,
    SwayCommandError,
    SwayProtocolError,
    get_outputs,
)
from swaydeck.sway import _parse_outputs


class ParseOutputsTests(unittest.TestCase):
    def test_parse_valid_outputs(self):
        outputs = _parse_outputs(
            """
            [
              {
                "name": "eDP-1",
                "active": true,
                "rect": {
                  "x": 0,
                  "y": 0,
                  "width": 1920,
                  "height": 1200
                },
                "scale": 1.5,
                "transform": "normal"
              },
              {
                "name": "HDMI-A-1",
                "active": false,
                "rect": {
                  "x": 0,
                  "y": 0,
                  "width": 0,
                  "height": 0
                },
                "scale": 1.0
              }
            ]
            """
        )

        self.assertEqual(len(outputs), 2)
        self.assertEqual(outputs[0].name, "eDP-1")
        self.assertTrue(outputs[0].active)
        self.assertEqual(
            outputs[0].rect,
            Rect(0, 0, 1920, 1200),
        )
        self.assertEqual(outputs[0].scale, 1.5)

        self.assertEqual(outputs[1].name, "HDMI-A-1")
        self.assertFalse(outputs[1].active)

    def test_invalid_json_is_rejected(self):
        with self.assertRaisesRegex(
            SwayProtocolError,
            "invalid JSON",
        ):
            _parse_outputs("{not-json")

    def test_non_array_response_is_rejected(self):
        with self.assertRaisesRegex(
            SwayProtocolError,
            "JSON array",
        ):
            _parse_outputs('{"name": "eDP-1"}')

    def test_missing_output_name_is_rejected(self):
        with self.assertRaisesRegex(
            SwayProtocolError,
            "has no name",
        ):
            _parse_outputs('[{"active": true}]')


class GetOutputsTests(unittest.TestCase):
    @patch("swaydeck.sway.subprocess.run")
    def test_get_outputs_uses_read_only_swaymsg_command(self, run):
        run.return_value = subprocess.CompletedProcess(
            args=["swaymsg", "-r", "-t", "get_outputs"],
            returncode=0,
            stdout='[{"name":"eDP-1","active":true}]',
            stderr="",
        )

        outputs = get_outputs()

        run.assert_called_once_with(
            ["swaymsg", "-r", "-t", "get_outputs"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5.0,
        )

        self.assertEqual(len(outputs), 1)
        self.assertEqual(outputs[0].name, "eDP-1")

    @patch("swaydeck.sway.subprocess.run")
    def test_nonzero_exit_is_reported(self, run):
        run.return_value = subprocess.CompletedProcess(
            args=["swaymsg"],
            returncode=1,
            stdout="",
            stderr="Unable to retrieve socket path",
        )

        with self.assertRaisesRegex(
            SwayCommandError,
            "Unable to retrieve socket path",
        ):
            get_outputs()

    @patch("swaydeck.sway.subprocess.run")
    def test_timeout_is_reported(self, run):
        run.side_effect = subprocess.TimeoutExpired(
            cmd=["swaymsg"],
            timeout=2,
        )

        with self.assertRaisesRegex(
            SwayCommandError,
            "timed out",
        ):
            get_outputs(timeout=2)

    @patch("swaydeck.sway.subprocess.run")
    def test_missing_swaymsg_is_reported(self, run):
        run.side_effect = FileNotFoundError

        with self.assertRaisesRegex(
            SwayCommandError,
            "not installed",
        ):
            get_outputs()


if __name__ == "__main__":
    unittest.main()
