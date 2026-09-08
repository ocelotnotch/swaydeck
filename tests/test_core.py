"""Behavioral tests for the incremental Python migration."""

import pathlib
import sys
import unittest

SRC = pathlib.Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from swaydeck import (
    Output,
    Rect,
    projection_mode,
    select_primary,
    two_layout_direction,
)


class PrimaryOutputTests(unittest.TestCase):
    def test_valid_override_wins(self):
        outputs = [
            Output("eDP-1", True),
            Output("HDMI-A-1", True),
        ]

        self.assertEqual(
            select_primary(outputs, "HDMI-A-1"),
            "HDMI-A-1",
        )

    def test_edp_is_default_primary(self):
        outputs = [
            Output("HDMI-A-1", True),
            Output("eDP-1", False),
        ]

        self.assertEqual(
            select_primary(outputs),
            "eDP-1",
        )

    def test_primary_fallbacks(self):
        self.assertEqual(
            select_primary([
                Output("DP-1", False),
                Output("HDMI-A-1", True),
            ]),
            "HDMI-A-1",
        )

        self.assertEqual(
            select_primary([Output("DP-1", False)]),
            "DP-1",
        )

        self.assertIsNone(select_primary([]))


class ProjectionModeTests(unittest.TestCase):
    def test_projection_modes_match_current_contract(self):
        primary = "eDP-1"

        cases = [
            (
                [
                    Output(primary, True),
                    Output("HDMI-A-1", False),
                ],
                False,
                "PC screen only",
            ),
            (
                [
                    Output(primary, False),
                    Output("HDMI-A-1", True),
                ],
                False,
                "Second screen only",
            ),
            (
                [
                    Output(primary, True),
                    Output("HDMI-A-1", True),
                ],
                False,
                "Extend",
            ),
            (
                [
                    Output(primary, True),
                    Output("HDMI-A-1", True),
                ],
                True,
                "Duplicate",
            ),
            (
                [
                    Output(primary, False),
                    Output("HDMI-A-1", False),
                ],
                False,
                "Unknown",
            ),
        ]

        for outputs, mirror_active, expected in cases:
            with self.subTest(expected=expected):
                self.assertEqual(
                    projection_mode(
                        outputs,
                        primary,
                        mirror_active=mirror_active,
                    ),
                    expected,
                )


class DirectionTests(unittest.TestCase):
    primary = Output(
        "eDP-1",
        True,
        Rect(0, 0, 1920, 1080),
    )

    def test_cardinal_directions(self):
        cases = [
            (Rect(1920, 0, 1920, 1080), "Right"),
            (Rect(-1920, 0, 1920, 1080), "Left"),
            (Rect(0, -1080, 1920, 1080), "Above"),
            (Rect(0, 1080, 1920, 1080), "Below"),
        ]

        for rect, expected in cases:
            with self.subTest(expected=expected):
                external = Output(
                    "HDMI-A-1",
                    True,
                    rect,
                )

                self.assertEqual(
                    two_layout_direction(
                        self.primary,
                        external,
                    ),
                    expected,
                )

    def test_offset_layout_uses_center_fallback(self):
        external = Output(
            "HDMI-A-1",
            True,
            Rect(1200, 250, 1920, 1080),
        )

        self.assertEqual(
            two_layout_direction(
                self.primary,
                external,
            ),
            "Right",
        )

    def test_missing_geometry_is_rejected(self):
        with self.assertRaises(ValueError):
            two_layout_direction(
                self.primary,
                Output("HDMI-A-1", True),
            )


class OutputModelTests(unittest.TestCase):
    def test_parse_sway_output(self):
        output = Output.from_sway({
            "name": "eDP-1",
            "active": True,
            "rect": {
                "x": 0,
                "y": 0,
                "width": 1920,
                "height": 1200,
            },
            "scale": 1.5,
            "transform": "normal",
        })

        self.assertEqual(
            output.rect,
            Rect(0, 0, 1920, 1200),
        )
        self.assertEqual(output.scale, 1.5)
        self.assertEqual(output.transform, "normal")


if __name__ == "__main__":
    unittest.main()
