"""Tests for SwayDeck display-operation planning."""

import pathlib
import sys
import unittest

SRC = pathlib.Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from swaydeck import (
    DisableOp,
    EnableOp,
    Output,
    PositionOp,
    Rect,
    plan_arrange_multi,
    plan_arrange_two,
    plan_pc_only,
    plan_right_chain,
    plan_second_only,
)


class PcOnlyPlanTests(unittest.TestCase):
    def test_pc_only_operation_order(self):
        outputs = [
            Output("eDP-1", True),
            Output("HDMI-A-1", True),
            Output("DP-1", False),
        ]

        self.assertEqual(
            plan_pc_only(
                outputs,
                "eDP-1",
            ),
            [
                EnableOp("eDP-1"),
                PositionOp("eDP-1", 0, 0),
                DisableOp("HDMI-A-1"),
                DisableOp("DP-1"),
            ],
        )

    def test_unknown_primary_is_rejected(self):
        with self.assertRaisesRegex(
            ValueError,
            "primary output not found",
        ):
            plan_pc_only(
                [Output("eDP-1", True)],
                "DP-99",
            )


class SecondOnlyPlanTests(unittest.TestCase):
    def test_destination_is_enabled_before_primary_is_disabled(self):
        outputs = [
            Output("eDP-1", True),
            Output("HDMI-A-1", False),
        ]

        self.assertEqual(
            plan_second_only(
                outputs,
                "eDP-1",
                "HDMI-A-1",
            ),
            [
                EnableOp("HDMI-A-1"),
                PositionOp("HDMI-A-1", 0, 0),
                DisableOp("eDP-1"),
            ],
        )

    def test_other_external_outputs_are_disabled(self):
        outputs = [
            Output("eDP-1", True),
            Output("HDMI-A-1", False),
            Output("DP-1", True),
            Output("DP-2", False),
        ]

        self.assertEqual(
            plan_second_only(
                outputs,
                "eDP-1",
                "DP-1",
            ),
            [
                EnableOp("DP-1"),
                PositionOp("DP-1", 0, 0),
                DisableOp("HDMI-A-1"),
                DisableOp("DP-2"),
                DisableOp("eDP-1"),
            ],
        )

    def test_target_cannot_be_primary(self):
        outputs = [
            Output("eDP-1", True),
        ]

        with self.assertRaisesRegex(
            ValueError,
            "must differ",
        ):
            plan_second_only(
                outputs,
                "eDP-1",
                "eDP-1",
            )

    def test_unknown_target_is_rejected(self):
        outputs = [
            Output("eDP-1", True),
            Output("HDMI-A-1", False),
        ]

        with self.assertRaisesRegex(
            ValueError,
            "target output not found",
        ):
            plan_second_only(
                outputs,
                "eDP-1",
                "DP-99",
            )



class ArrangeTwoPlanTests(unittest.TestCase):
    def test_cardinal_directions(self):
        anchor = Output(
            "eDP-1",
            True,
            rect=Rect(
                500,
                300,
                1920,
                1080,
            ),
        )

        target = Output(
            "HDMI-A-1",
            True,
            rect=Rect(
                100,
                100,
                1280,
                720,
            ),
        )

        cases = [
            (
                "Right",
                [
                    PositionOp("eDP-1", 0, 0),
                    PositionOp("HDMI-A-1", 1920, 0),
                ],
            ),
            (
                "Left",
                [
                    PositionOp("HDMI-A-1", 0, 0),
                    PositionOp("eDP-1", 1280, 0),
                ],
            ),
            (
                "Above",
                [
                    PositionOp("HDMI-A-1", 0, 0),
                    PositionOp("eDP-1", 0, 720),
                ],
            ),
            (
                "Below",
                [
                    PositionOp("eDP-1", 0, 0),
                    PositionOp("HDMI-A-1", 0, 1080),
                ],
            ),
        ]

        for direction, expected in cases:
            with self.subTest(direction=direction):
                self.assertEqual(
                    plan_arrange_two(
                        anchor,
                        target,
                        direction,
                    ),
                    expected,
                )

    def test_requires_geometry(self):
        with self.assertRaisesRegex(
            ValueError,
            "has no geometry",
        ):
            plan_arrange_two(
                Output("eDP-1", True),
                Output(
                    "HDMI-A-1",
                    True,
                    rect=Rect(
                        0,
                        0,
                        1920,
                        1080,
                    ),
                ),
                "Right",
            )


class ArrangeMultiPlanTests(unittest.TestCase):
    def test_negative_canvas_is_normalized(self):
        outputs = [
            Output(
                "eDP-1",
                True,
                Rect(0, 0, 1920, 1080),
            ),
            Output(
                "HDMI-A-1",
                True,
                Rect(1920, 0, 1280, 1024),
            ),
            Output(
                "DP-1",
                True,
                Rect(3200, 0, 1024, 768),
            ),
        ]

        self.assertEqual(
            plan_arrange_multi(
                outputs,
                "DP-1",
                "eDP-1",
                "Left",
            ),
            [
                PositionOp(
                    "eDP-1",
                    1024,
                    0,
                ),
                PositionOp(
                    "HDMI-A-1",
                    2944,
                    0,
                ),
                PositionOp(
                    "DP-1",
                    0,
                    0,
                ),
            ],
        )

    def test_inactive_target_is_rejected(self):
        outputs = [
            Output(
                "eDP-1",
                True,
                Rect(0, 0, 1920, 1080),
            ),
            Output(
                "HDMI-A-1",
                False,
                Rect(1920, 0, 1920, 1080),
            ),
        ]

        with self.assertRaisesRegex(
            ValueError,
            "active target output not found",
        ):
            plan_arrange_multi(
                outputs,
                "HDMI-A-1",
                "eDP-1",
                "Right",
            )

    def test_target_and_anchor_must_differ(self):
        outputs = [
            Output(
                "eDP-1",
                True,
                Rect(0, 0, 1920, 1080),
            ),
        ]

        with self.assertRaisesRegex(
            ValueError,
            "must differ",
        ):
            plan_arrange_multi(
                outputs,
                "eDP-1",
                "eDP-1",
                "Right",
            )


class RightChainPlanTests(unittest.TestCase):
    def test_positions_outputs_from_left_to_right(self):
        outputs = [
            Output(
                "eDP-1",
                True,
                Rect(500, 300, 1920, 1080),
            ),
            Output(
                "HDMI-A-1",
                True,
                Rect(0, 0, 1280, 1024),
            ),
            Output(
                "DP-1",
                True,
                Rect(0, 0, 1024, 768),
            ),
        ]

        self.assertEqual(
            plan_right_chain(
                outputs,
                "eDP-1",
            ),
            [
                PositionOp(
                    "eDP-1",
                    0,
                    0,
                ),
                PositionOp(
                    "HDMI-A-1",
                    1920,
                    0,
                ),
                PositionOp(
                    "DP-1",
                    3200,
                    0,
                ),
            ],
        )

    def test_requires_active_outputs(self):
        outputs = [
            Output(
                "eDP-1",
                True,
                Rect(0, 0, 1920, 1080),
            ),
            Output(
                "HDMI-A-1",
                False,
                Rect(0, 0, 1280, 1024),
            ),
        ]

        with self.assertRaisesRegex(
            ValueError,
            "must be active",
        ):
            plan_right_chain(
                outputs,
                "eDP-1",
            )

    def test_requires_geometry(self):
        with self.assertRaisesRegex(
            ValueError,
            "has no geometry",
        ):
            plan_right_chain(
                [
                    Output(
                        "eDP-1",
                        True,
                    ),
                ],
                "eDP-1",
            )

if __name__ == "__main__":
    unittest.main()
