"""Tests for persistent layouts."""

import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

SRC = pathlib.Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from swaydeck import (
    LayoutError,
    generate_layout_config,
    layout_signature,
    save_current_layout,
)


def active_output(
    name: str = "eDP-1",
    *,
    x: int = 0,
    y: int = 0,
):
    return {
        "name": name,
        "active": True,
        "current_mode": {
            "width": 2880,
            "height": 1800,
            "refresh": 90001,
        },
        "scale": 1.5,
        "transform": "normal",
        "rect": {
            "x": x,
            "y": y,
            "width": 1920,
            "height": 1200,
        },
    }


class LayoutSerializationTests(unittest.TestCase):
    def test_generates_layout(self):
        content = generate_layout_config(
            [
                active_output(),
                {
                    "name": "HDMI-A-1",
                    "active": False,
                },
            ]
        )

        self.assertIn(
            (
                "output eDP-1 mode "
                "2880x1800@90.001Hz "
                "scale 1.5 "
                "transform normal "
                "position 0 0"
            ),
            content,
        )

        self.assertIn(
            "output HDMI-A-1 disable",
            content,
        )

    def test_unsafe_name_rejected(self):
        with self.assertRaisesRegex(
            LayoutError,
            "unsafe output name",
        ):
            generate_layout_config(
                [
                    {
                        "name": "bad output",
                        "active": False,
                    }
                ]
            )

    def test_signature_order_independent(self):
        a = active_output()

        b = {
            "name": "HDMI-A-1",
            "active": False,
        }

        self.assertEqual(
            layout_signature([a, b]),
            layout_signature([b, a]),
        )


class LayoutSaveTests(unittest.TestCase):
    @patch(
        "swaydeck.layout.mirror_alive",
        return_value=True,
    )
    def test_duplicate_cannot_be_saved(
        self,
        alive,
    ):
        with self.assertRaisesRegex(
            LayoutError,
            "cannot be persisted",
        ):
            save_current_layout()

    @patch("swaydeck.layout._reload_sway")
    @patch("swaydeck.layout._validate_candidate")
    @patch("swaydeck.layout._read_raw_outputs")
    @patch(
        "swaydeck.layout.mirror_alive",
        return_value=False,
    )
    def test_atomic_save(
        self,
        alive,
        read_outputs,
        validate,
        reload_sway,
    ):
        state = [
            active_output()
        ]

        read_outputs.side_effect = [
            state,
            state,
        ]

        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)

            destination = (
                root
                / "layout.conf"
            )

            result = save_current_layout(
                layout_file=destination,
                backup_dir=root / "backups",
                verify_delay=0,
            )

            self.assertEqual(
                result,
                destination,
            )

            self.assertTrue(
                destination.exists()
            )

    @patch("swaydeck.layout._reload_sway")
    @patch("swaydeck.layout._validate_candidate")
    @patch("swaydeck.layout._read_raw_outputs")
    @patch(
        "swaydeck.layout.mirror_alive",
        return_value=False,
    )
    def test_mismatch_rolls_back(
        self,
        alive,
        read_outputs,
        validate,
        reload_sway,
    ):
        before = [
            active_output()
        ]

        after = [
            active_output(
                x=1920,
            )
        ]

        read_outputs.side_effect = [
            before,
            after,
        ]

        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)

            destination = (
                root
                / "layout.conf"
            )

            destination.write_text(
                "old-layout\n"
            )

            with self.assertRaisesRegex(
                LayoutError,
                "previous layout restored",
            ):
                save_current_layout(
                    layout_file=destination,
                    backup_dir=root / "backups",
                    verify_delay=0,
                )

            self.assertEqual(
                destination.read_text(),
                "old-layout\n",
            )


if __name__ == "__main__":
    unittest.main()
