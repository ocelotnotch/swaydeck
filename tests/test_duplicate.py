"""Tests for SwayDeck Duplicate workflow."""

import pathlib
import sys
import unittest
from unittest.mock import patch

SRC = pathlib.Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from swaydeck import (
    MirrorError,
    Output,
    WorkflowError,
    apply_duplicate,
)


class DuplicateWorkflowTests(unittest.TestCase):
    @patch(
        "swaydeck.workflows.start_mirror",
        return_value=(101,),
    )
    @patch("swaydeck.workflows.apply_extend_right")
    @patch("swaydeck.workflows.get_outputs")
    @patch(
        "swaydeck.workflows.require_wl_mirror",
        return_value="/usr/bin/wl-mirror",
    )
    @patch("swaydeck.workflows.stop_mirror")
    def test_duplicate_extends_then_starts_mirror(
        self,
        stop,
        require,
        get_outputs,
        extend,
        start,
    ):
        get_outputs.return_value = [
            Output("eDP-1", True),
            Output("HDMI-A-1", False),
        ]

        result = apply_duplicate(
            settle_seconds=0,
            verify_delay=0,
        )

        self.assertEqual(
            result,
            (101,),
        )

        stop.assert_called_once_with()
        require.assert_called_once_with()

        extend.assert_called_once_with(
            primary_override="eDP-1",
            settle_seconds=0,
        )

        start.assert_called_once_with(
            "eDP-1",
            ("HDMI-A-1",),
            verify_delay=0,
        )

    @patch("swaydeck.workflows.start_mirror")
    @patch("swaydeck.workflows.apply_extend_right")
    @patch("swaydeck.workflows.get_outputs")
    @patch(
        "swaydeck.workflows.require_wl_mirror",
        return_value="/usr/bin/wl-mirror",
    )
    @patch("swaydeck.workflows.stop_mirror")
    def test_external_output_is_required(
        self,
        stop,
        require,
        get_outputs,
        extend,
        start,
    ):
        get_outputs.return_value = [
            Output("eDP-1", True),
        ]

        with self.assertRaisesRegex(
            WorkflowError,
            "no external outputs",
        ):
            apply_duplicate()

        extend.assert_not_called()
        start.assert_not_called()

    @patch("swaydeck.workflows.start_mirror")
    @patch("swaydeck.workflows.apply_extend_right")
    @patch("swaydeck.workflows.get_outputs")
    @patch("swaydeck.workflows.require_wl_mirror")
    @patch("swaydeck.workflows.stop_mirror")
    def test_missing_binary_prevents_layout_mutation(
        self,
        stop,
        require,
        get_outputs,
        extend,
        start,
    ):
        require.side_effect = MirrorError(
            "wl-mirror is not installed"
        )

        with self.assertRaisesRegex(
            MirrorError,
            "not installed",
        ):
            apply_duplicate()

        stop.assert_called_once_with()
        get_outputs.assert_not_called()
        extend.assert_not_called()
        start.assert_not_called()

    @patch("swaydeck.workflows.start_mirror")
    @patch("swaydeck.workflows.apply_extend_right")
    @patch("swaydeck.workflows.get_outputs")
    @patch(
        "swaydeck.workflows.require_wl_mirror",
        return_value="/usr/bin/wl-mirror",
    )
    @patch("swaydeck.workflows.stop_mirror")
    def test_primary_override_is_preserved(
        self,
        stop,
        require,
        get_outputs,
        extend,
        start,
    ):
        get_outputs.return_value = [
            Output("eDP-1", True),
            Output("HDMI-A-1", True),
        ]

        start.return_value = (202,)

        result = apply_duplicate(
            primary_override="HDMI-A-1",
            settle_seconds=0,
            verify_delay=0,
        )

        self.assertEqual(
            result,
            (202,),
        )

        extend.assert_called_once_with(
            primary_override="HDMI-A-1",
            settle_seconds=0,
        )

        start.assert_called_once_with(
            "HDMI-A-1",
            ("eDP-1",),
            verify_delay=0,
        )


if __name__ == "__main__":
    unittest.main()
