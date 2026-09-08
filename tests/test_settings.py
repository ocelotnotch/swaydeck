"""Tests for display settings."""

import pathlib
import sys
import unittest
from unittest.mock import patch

SRC = pathlib.Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from swaydeck import (
    Output,
    Rect,
    SettingsError,
    apply_orientation,
    apply_scale,
    transform_label,
)


def current_outputs():
    return [
        Output(
            "eDP-1",
            True,
            Rect(
                0,
                0,
                1920,
                1200,
            ),
            1.5,
            "normal",
        ),
        Output(
            "HDMI-A-1",
            True,
            Rect(
                1920,
                0,
                1920,
                1080,
            ),
            1.0,
            "normal",
        ),
    ]


class SettingsTests(unittest.TestCase):
    def test_transform_label(self):
        self.assertEqual(
            transform_label("90"),
            "Portrait",
        )

    @patch(
        "swaydeck.settings.mirror_alive",
        return_value=True,
    )
    def test_duplicate_blocks_settings(
        self,
        alive,
    ):
        with self.assertRaisesRegex(
            SettingsError,
            "Duplicate",
        ):
            apply_scale(
                "eDP-1",
                1.5,
            )

    @patch("swaydeck.settings.arrange_displays")
    @patch("swaydeck.settings.scale_output")
    @patch("swaydeck.settings.get_outputs")
    @patch(
        "swaydeck.settings.mirror_alive",
        return_value=False,
    )
    def test_scale_restores_direction(
        self,
        alive,
        get_outputs,
        scale,
        arrange,
    ):
        get_outputs.side_effect = [
            current_outputs(),
            current_outputs(),
        ]

        apply_scale(
            "eDP-1",
            1.5,
            settle_seconds=0,
        )

        scale.assert_called_once_with(
            "eDP-1",
            1.5,
        )

        arrange.assert_called_once_with(
            "HDMI-A-1",
            "eDP-1",
            "Right",
        )

    @patch("swaydeck.settings.arrange_displays")
    @patch("swaydeck.settings.transform_output")
    @patch("swaydeck.settings.get_outputs")
    @patch(
        "swaydeck.settings.mirror_alive",
        return_value=False,
    )
    def test_orientation_restores_direction(
        self,
        alive,
        get_outputs,
        transform,
        arrange,
    ):
        get_outputs.side_effect = [
            current_outputs(),
            current_outputs(),
        ]

        apply_orientation(
            "HDMI-A-1",
            "90",
            settle_seconds=0,
        )

        transform.assert_called_once_with(
            "HDMI-A-1",
            "90",
        )

        arrange.assert_called_once_with(
            "HDMI-A-1",
            "eDP-1",
            "Right",
        )


if __name__ == "__main__":
    unittest.main()
