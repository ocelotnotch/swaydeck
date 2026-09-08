"""Keep release metadata synchronized."""

from __future__ import annotations

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ReleaseMetadataTests(unittest.TestCase):
    def test_release_metadata_matches_pyproject(self):
        pyproject = (
            ROOT / "pyproject.toml"
        ).read_text()

        match = re.search(
            r'^version = "([^"]+)"$',
            pyproject,
            re.MULTILINE,
        )

        self.assertIsNotNone(match)
        version = match.group(1)

        cli = (
            ROOT
            / "src"
            / "swaydeck"
            / "cli.py"
        ).read_text()

        self.assertIn(
            f'APP_VERSION = "{version}"',
            cli,
        )

        readme = (
            ROOT / "README.md"
        ).read_text()

        self.assertIn(
            (
                "Latest release:\n\n"
                "```text\n"
                f"v{version}\n"
                "```"
            ),
            readme,
        )

        self.assertIn(
            (
                "Current version on `main`:\n\n"
                "```text\n"
                f"{version}\n"
                "```"
            ),
            readme,
        )

        changelog = (
            ROOT / "CHANGELOG.md"
        ).read_text()

        self.assertRegex(
            changelog,
            rf"(?m)^## v{re.escape(version)}\b",
        )


if __name__ == "__main__":
    unittest.main()
