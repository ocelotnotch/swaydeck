"""Run with python3 -m unittest discover -s tests."""
import pathlib
import runpy
import unittest

format_outputs = runpy.run_path(str(
    pathlib.Path(__file__).resolve().parents[1] / "contrib/waybar/swaydeck-waybar"
))["format_outputs"]


def output(name, active=True):
    return {"name": name, "active": active, "current_mode":
            {"width": 2880, "height": 1800, "refresh": 90001} if active else None}


class WaybarTests(unittest.TestCase):
    def test_agreed_layouts(self):
        for outputs, text in [
            ([output("eDP-1")], "\uf108"),
            ([output("eDP-1"), output("HDMI-A-1")], "\uf108 2"),
            ([output("eDP-1"), output("HDMI-A-1"), output("DP-1")], "\uf108 3"),
            ([output("eDP-1", False), output("HDMI-A-1")], "\uf108"),
        ]:
            with self.subTest(outputs=outputs):
                self.assertEqual(format_outputs(outputs)["text"], text)

    def test_tooltip_and_inactive_display(self):
        result = format_outputs([output("eDP-1"), output("HDMI-A-1", False)])
        self.assertIn("eDP-1 · Active · 2880×1800 · 90 Hz", result["tooltip"])
        self.assertIn("HDMI-A-1 · Inactive", result["tooltip"])
        self.assertIn("1 active display", result["tooltip"])

    def test_markup_and_zero_outputs(self):
        self.assertIn("A&lt;&amp;&gt;", format_outputs([output("A<&>")])["tooltip"])
        self.assertEqual(format_outputs([])["text"], "\uf108")
        self.assertIn("0 active displays", format_outputs([])["tooltip"])


if __name__ == "__main__":
    unittest.main()
