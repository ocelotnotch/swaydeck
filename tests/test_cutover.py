"""Static tests for Python cutover."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class CutoverTests(unittest.TestCase):
    def test_root_launcher_is_python(self):
        content = (
            ROOT
            / "swaydeck"
        ).read_text()

        self.assertTrue(
            content.startswith(
                "#!/usr/bin/env python3"
            )
        )

    def test_legacy_bash_exists(self):
        path = (
            ROOT
            / "legacy"
            / "swaydeck.bash"
        )

        self.assertTrue(
            path.exists()
        )

        self.assertTrue(
            path.read_text().startswith(
                "#!/usr/bin/env bash"
            )
        )

    def test_pyproject_entrypoint(self):
        content = (
            ROOT
            / "pyproject.toml"
        ).read_text()

        self.assertIn(
            'swaydeck = "swaydeck.cli:main"',
            content,
        )

    def test_root_launcher_is_executable(self):
        path = (
            ROOT
            / "swaydeck"
        )

        self.assertTrue(
            path.stat().st_mode
            & 0o111
        )


if __name__ == "__main__":
    unittest.main()
