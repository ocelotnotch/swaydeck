"""Tests for complete SwayDeck display workflows."""

import pathlib
import sys
import unittest
from unittest.mock import call, patch

SRC = pathlib.Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from swaydeck import (
    DisableOp,
    EnableOp,
    Output,
    PositionOp,
    Rect,
    WorkflowError,
    apply_extend_right,
    apply_pc_only,
    apply_second_only,
    arrange_displays,
)


class PcOnlyWorkflowTests(unittest.TestCase):
    @patch("swaydeck.workflows.execute_operations")
    @patch("swaydeck.workflows.get_outputs")
    def test_pc_only_builds_and_executes_plan(
        self,
        get_outputs,
        execute,
    ):
        get_outputs.return_value = [
            Output(
                "eDP-1",
                True,
            ),
            Output(
                "HDMI-A-1",
                True,
            ),
        ]

        operations = apply_pc_only()

        expected = [
            EnableOp("eDP-1"),
            PositionOp(
                "eDP-1",
                0,
                0,
            ),
            DisableOp("HDMI-A-1"),
        ]

        self.assertEqual(
            operations,
            expected,
        )

        execute.assert_called_once_with(
            expected
        )

    @patch("swaydeck.workflows.execute_operations")
    @patch("swaydeck.workflows.get_outputs")
    def test_no_outputs_is_rejected(
        self,
        get_outputs,
        execute,
    ):
        get_outputs.return_value = []

        with self.assertRaisesRegex(
            WorkflowError,
            "no Sway outputs",
        ):
            apply_pc_only()

        execute.assert_not_called()


class SecondOnlyWorkflowTests(unittest.TestCase):
    @patch("swaydeck.workflows.execute_operations")
    @patch("swaydeck.workflows.get_outputs")
    def test_second_only_preserves_safety_order(
        self,
        get_outputs,
        execute,
    ):
        get_outputs.return_value = [
            Output(
                "eDP-1",
                True,
            ),
            Output(
                "HDMI-A-1",
                False,
            ),
        ]

        operations = apply_second_only(
            "HDMI-A-1"
        )

        expected = [
            EnableOp("HDMI-A-1"),
            PositionOp(
                "HDMI-A-1",
                0,
                0,
            ),
            DisableOp("eDP-1"),
        ]

        self.assertEqual(
            operations,
            expected,
        )

        execute.assert_called_once_with(
            expected
        )


class ExtendWorkflowTests(unittest.TestCase):
    @patch("swaydeck.workflows.time.sleep")
    @patch("swaydeck.workflows.execute_operations")
    @patch("swaydeck.workflows.get_outputs")
    def test_extend_reloads_geometry_after_enable(
        self,
        get_outputs,
        execute,
        sleep,
    ):
        get_outputs.side_effect = [
            [
                Output(
                    "eDP-1",
                    True,
                    Rect(
                        0,
                        0,
                        1920,
                        1080,
                    ),
                ),
                Output(
                    "HDMI-A-1",
                    False,
                ),
            ],
            [
                Output(
                    "eDP-1",
                    True,
                    Rect(
                        0,
                        0,
                        1920,
                        1080,
                    ),
                ),
                Output(
                    "HDMI-A-1",
                    True,
                    Rect(
                        1920,
                        0,
                        1280,
                        720,
                    ),
                ),
            ],
        ]

        operations = apply_extend_right()

        enable_plan = [
            EnableOp("eDP-1"),
            EnableOp("HDMI-A-1"),
        ]

        position_plan = [
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
        ]

        self.assertEqual(
            operations,
            [
                *enable_plan,
                *position_plan,
            ],
        )

        self.assertEqual(
            execute.call_args_list,
            [
                call(enable_plan),
                call(position_plan),
            ],
        )

        self.assertEqual(
            get_outputs.call_count,
            2,
        )

        sleep.assert_called_once_with(
            0.15
        )

    @patch("swaydeck.workflows.get_outputs")
    @patch("swaydeck.workflows.execute_operations")
    def test_extend_stops_if_enable_stage_fails(
        self,
        execute,
        get_outputs,
    ):
        get_outputs.return_value = [
            Output(
                "eDP-1",
                True,
                Rect(
                    0,
                    0,
                    1920,
                    1080,
                ),
            ),
            Output(
                "HDMI-A-1",
                False,
            ),
        ]

        execute.side_effect = RuntimeError(
            "enable failed"
        )

        with self.assertRaisesRegex(
            RuntimeError,
            "enable failed",
        ):
            apply_extend_right(
                settle_seconds=0,
            )

        self.assertEqual(
            get_outputs.call_count,
            1,
        )

        self.assertEqual(
            execute.call_count,
            1,
        )


class ArrangeWorkflowTests(unittest.TestCase):
    @patch("swaydeck.workflows.execute_operations")
    @patch("swaydeck.workflows.get_outputs")
    def test_two_monitor_arrangement(
        self,
        get_outputs,
        execute,
    ):
        get_outputs.return_value = [
            Output(
                "eDP-1",
                True,
                Rect(
                    0,
                    0,
                    1920,
                    1080,
                ),
            ),
            Output(
                "HDMI-A-1",
                True,
                Rect(
                    1920,
                    0,
                    1280,
                    720,
                ),
            ),
        ]

        operations = arrange_displays(
            "HDMI-A-1",
            "eDP-1",
            "Above",
        )

        expected = [
            PositionOp(
                "HDMI-A-1",
                0,
                0,
            ),
            PositionOp(
                "eDP-1",
                0,
                720,
            ),
        ]

        self.assertEqual(
            operations,
            expected,
        )

        execute.assert_called_once_with(
            expected
        )

    @patch("swaydeck.workflows.execute_operations")
    @patch("swaydeck.workflows.get_outputs")
    def test_multi_monitor_arrangement(
        self,
        get_outputs,
        execute,
    ):
        get_outputs.return_value = [
            Output(
                "eDP-1",
                True,
                Rect(
                    0,
                    0,
                    1920,
                    1080,
                ),
            ),
            Output(
                "HDMI-A-1",
                True,
                Rect(
                    1920,
                    0,
                    1280,
                    720,
                ),
            ),
            Output(
                "DP-1",
                True,
                Rect(
                    3200,
                    0,
                    1024,
                    768,
                ),
            ),
        ]

        operations = arrange_displays(
            "DP-1",
            "eDP-1",
            "Left",
        )

        expected = [
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
        ]

        self.assertEqual(
            operations,
            expected,
        )

        execute.assert_called_once_with(
            expected
        )

    @patch("swaydeck.workflows.execute_operations")
    @patch("swaydeck.workflows.get_outputs")
    def test_arrange_requires_two_active_outputs(
        self,
        get_outputs,
        execute,
    ):
        get_outputs.return_value = [
            Output(
                "eDP-1",
                True,
            ),
            Output(
                "HDMI-A-1",
                False,
            ),
        ]

        with self.assertRaisesRegex(
            WorkflowError,
            "at least two active outputs",
        ):
            arrange_displays(
                "HDMI-A-1",
                "eDP-1",
                "Right",
            )

        execute.assert_not_called()


if __name__ == "__main__":
    unittest.main()
