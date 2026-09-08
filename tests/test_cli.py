"""Tests for SwayDeck CLI."""

import io
import pathlib
import sys
import unittest
from contextlib import (
    redirect_stderr,
    redirect_stdout,
)
from unittest.mock import patch

SRC = pathlib.Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from swaydeck.cli import main
from swaydeck.layout import LayoutError


class CliTests(unittest.TestCase):
    def test_version(self):
        output = io.StringIO()

        with redirect_stdout(output):
            result = main(
                ["--version"]
            )

        self.assertEqual(
            result,
            0,
        )

        self.assertIn(
            "SwayDeck 0.3.0",
            output.getvalue(),
        )

    def test_help(self):
        output = io.StringIO()

        with redirect_stdout(output):
            result = main(
                ["--help"]
            )

        self.assertEqual(
            result,
            0,
        )

        self.assertIn(
            "--save-layout",
            output.getvalue(),
        )

    @patch(
        "swaydeck.cli.run_tui",
        return_value=0,
    )
    def test_default_runs_tui(
        self,
        run_tui,
    ):
        self.assertEqual(
            main([]),
            0,
        )

        run_tui.assert_called_once_with()

    @patch(
        "swaydeck.cli.save_current_layout",
        side_effect=LayoutError(
            "failed"
        ),
    )
    def test_save_failure_returns_one(
        self,
        save,
    ):
        error = io.StringIO()

        with redirect_stderr(error):
            result = main(
                ["--save-layout"]
            )

        self.assertEqual(
            result,
            1,
        )


if __name__ == "__main__":
    unittest.main()
