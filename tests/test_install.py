"""Integration tests for SwayDeck installation lifecycle."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


def make_fake_command(
    directory: Path,
    name: str,
) -> None:
    path = directory / name

    path.write_text(
        "#!/usr/bin/env sh\n"
        "exit 0\n"
    )

    path.chmod(0o755)


class InstallerTests(unittest.TestCase):
    def make_environment(
        self,
        root: Path,
    ) -> tuple[Path, dict[str, str]]:
        home = root / "home"
        fake_bin = root / "fake-bin"

        home.mkdir()
        fake_bin.mkdir()

        make_fake_command(fake_bin, "swaymsg")
        make_fake_command(fake_bin, "fzf")

        env = os.environ.copy()

        env.update(
            {
                "HOME": str(home),
                "XDG_DATA_HOME": str(
                    home / ".local" / "share"
                ),
                "PATH": (
                    f"{fake_bin}:"
                    f"{env['PATH']}"
                ),
            }
        )

        return home, env

    def test_fresh_install_and_uninstall(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            home, env = self.make_environment(root)

            install = subprocess.run(
                ["bash", str(ROOT / "install.sh")],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(
                install.returncode,
                0,
                msg=install.stdout + install.stderr,
            )

            runtime = (
                home / ".local" / "share" / "swaydeck"
            )

            launcher = (
                home / ".local" / "bin" / "swaydeck"
            )

            compat = (
                home / ".local" / "bin" / "displayctl"
            )

            self.assertTrue(
                (
                    runtime
                    / "src"
                    / "swaydeck"
                    / "cli.py"
                ).is_file()
            )

            self.assertTrue(launcher.is_symlink())
            self.assertTrue(compat.is_symlink())

            version = subprocess.run(
                [str(launcher), "--version"],
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(
                version.returncode,
                0,
                msg=version.stderr,
            )

            self.assertEqual(
                version.stdout.strip(),
                "SwayDeck 0.3.2",
            )

            uninstall = subprocess.run(
                ["bash", str(ROOT / "uninstall.sh")],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(
                uninstall.returncode,
                0,
                msg=uninstall.stdout + uninstall.stderr,
            )

            self.assertFalse(launcher.exists())
            self.assertFalse(launcher.is_symlink())
            self.assertFalse(compat.exists())
            self.assertFalse(compat.is_symlink())
            self.assertFalse(runtime.exists())

    def test_failed_staged_validation_preserves_existing_install(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            home, env = self.make_environment(root)

            runtime = (
                home / ".local" / "share" / "swaydeck"
            )

            launcher = (
                home / ".local" / "bin" / "swaydeck"
            )

            runtime.mkdir(parents=True)
            launcher.parent.mkdir(parents=True)

            existing = runtime / "swaydeck"

            existing.write_text(
                "#!/usr/bin/env sh\n"
                "printf '%s\\n' 'existing-install'\n"
            )

            existing.chmod(0o755)
            launcher.symlink_to(existing)

            source = root / "broken-source"
            source.mkdir()

            shutil.copy2(
                ROOT / "install.sh",
                source / "install.sh",
            )

            shutil.copy2(
                ROOT / "swaydeck",
                source / "swaydeck",
            )

            shutil.copytree(
                ROOT / "src",
                source / "src",
            )

            main_file = (
                source
                / "src"
                / "swaydeck"
                / "__main__.py"
            )

            main_file.write_text(
                'raise RuntimeError("forced staged failure")\n'
                + main_file.read_text()
            )

            failed = subprocess.run(
                ["bash", str(source / "install.sh")],
                cwd=source,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertNotEqual(
                failed.returncode,
                0,
                msg="broken staged runtime unexpectedly installed",
            )

            self.assertTrue(existing.is_file())
            self.assertTrue(launcher.is_symlink())

            preserved = subprocess.run(
                [str(launcher)],
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(
                preserved.returncode,
                0,
                msg=preserved.stderr,
            )

            self.assertEqual(
                preserved.stdout.strip(),
                "existing-install",
            )

    def test_unrelated_displayctl_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            home, env = self.make_environment(root)

            compat = (
                home / ".local" / "bin" / "displayctl"
            )

            compat.parent.mkdir(parents=True)

            unrelated = root / "unrelated-tool"

            unrelated.write_text(
                "#!/usr/bin/env sh\n"
                "exit 0\n"
            )

            unrelated.chmod(0o755)
            compat.symlink_to(unrelated)

            install = subprocess.run(
                ["bash", str(ROOT / "install.sh")],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(
                install.returncode,
                0,
                msg=install.stdout + install.stderr,
            )

            self.assertTrue(compat.is_symlink())
            self.assertEqual(
                compat.resolve(),
                unrelated.resolve(),
            )

            uninstall = subprocess.run(
                ["bash", str(ROOT / "uninstall.sh")],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(
                uninstall.returncode,
                0,
                msg=uninstall.stdout + uninstall.stderr,
            )

            self.assertTrue(compat.is_symlink())
            self.assertEqual(
                compat.resolve(),
                unrelated.resolve(),
            )


if __name__ == "__main__":
    unittest.main()
