"""Regression tests for the fzf color contract."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest


SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from swaydeck.ui import FZF_THEME


class UIThemeTests(unittest.TestCase):
    def test_readable_transparent_palette(self):
        color_args = [
            value
            for value in FZF_THEME
            if value.startswith("--color=")
        ]

        self.assertEqual(
            len(color_args),
            1,
        )

        color = color_args[0]

        expected = (
            "fg:-1",
            "fg+:#c0caf5:bold",
            "hl:#7aa2f7",
            "hl+:#7aa2f7:bold",
            "info:#a9b1d6",
            "prompt:#7aa2f7:bold",
            "pointer:#7aa2f7:bold",
            "header:#a9b1d6",
            "border:#565f89",
            "bg:-1",
            "bg+:-1",
            "gutter:-1",
        )

        for token in expected:
            with self.subTest(token=token):
                self.assertIn(
                    token,
                    color,
                )

    def test_old_low_contrast_palette_is_gone(self):
        color = next(
            value
            for value in FZF_THEME
            if value.startswith("--color=")
        )

        old_tokens = (
            "fg:#565a6e",
            "fg+:#34548a:bold",
            "hl:#5a4a78",
            "hl+:#34548a:bold",
            "prompt:#34548a:bold",
            "pointer:#34548a:bold",
            "header:#343b58",
        )

        for token in old_tokens:
            with self.subTest(token=token):
                self.assertNotIn(
                    token,
                    color,
                )


if __name__ == "__main__":
    unittest.main()
