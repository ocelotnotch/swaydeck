"""Tests for planned display-operation execution."""

import pathlib
import sys
import unittest
from unittest.mock import call, patch

SRC = pathlib.Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from swaydeck import (
    DisableOp,
    EnableOp,
    PositionOp,
    execute_operation,
    execute_operations,
)


class ExecuteOperationTests(unittest.TestCase):
    @patch("swaydeck.executor.enable_output")
    def test_enable_operation(self, enable):
        execute_operation(
            EnableOp("eDP-1")
        )

        enable.assert_called_once_with(
            "eDP-1"
        )

    @patch("swaydeck.executor.disable_output")
    def test_disable_operation(self, disable):
        execute_operation(
            DisableOp("HDMI-A-1")
        )

        disable.assert_called_once_with(
            "HDMI-A-1"
        )

    @patch("swaydeck.executor.position_output")
    def test_position_operation(self, position):
        execute_operation(
            PositionOp(
                "HDMI-A-1",
                1920,
                -100,
            )
        )

        position.assert_called_once_with(
            "HDMI-A-1",
            1920,
            -100,
        )


class ExecuteOperationsTests(unittest.TestCase):
    @patch("swaydeck.executor.position_output")
    @patch("swaydeck.executor.disable_output")
    @patch("swaydeck.executor.enable_output")
    def test_operations_execute_in_exact_plan_order(
        self,
        enable,
        disable,
        position,
    ):
        timeline = []

        enable.side_effect = (
            lambda *args: timeline.append(
                ("enable", *args)
            )
        )

        disable.side_effect = (
            lambda *args: timeline.append(
                ("disable", *args)
            )
        )

        position.side_effect = (
            lambda *args: timeline.append(
                ("position", *args)
            )
        )

        execute_operations([
            EnableOp("HDMI-A-1"),
            PositionOp(
                "HDMI-A-1",
                0,
                0,
            ),
            DisableOp("eDP-1"),
        ])

        self.assertEqual(
            timeline,
            [
                (
                    "enable",
                    "HDMI-A-1",
                ),
                (
                    "position",
                    "HDMI-A-1",
                    0,
                    0,
                ),
                (
                    "disable",
                    "eDP-1",
                ),
            ],
        )

    @patch("swaydeck.executor.execute_operation")
    def test_execution_stops_on_first_failure(
        self,
        execute,
    ):
        execute.side_effect = [
            None,
            RuntimeError("boom"),
            None,
        ]

        operations = [
            EnableOp("eDP-1"),
            PositionOp(
                "eDP-1",
                0,
                0,
            ),
            DisableOp("HDMI-A-1"),
        ]

        with self.assertRaisesRegex(
            RuntimeError,
            "boom",
        ):
            execute_operations(
                operations
            )

        self.assertEqual(
            execute.call_args_list,
            [
                call(operations[0]),
                call(operations[1]),
            ],
        )

    @patch("swaydeck.executor.execute_operation")
    def test_empty_plan_is_noop(
        self,
        execute,
    ):
        execute_operations([])

        execute.assert_not_called()


if __name__ == "__main__":
    unittest.main()
