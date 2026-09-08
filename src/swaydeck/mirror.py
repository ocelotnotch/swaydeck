"""wl-mirror process lifecycle management for SwayDeck."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import signal
import subprocess
import time
from collections.abc import Iterable


class MirrorError(RuntimeError):
    """Raised when wl-mirror cannot be managed safely."""


def default_state_dir() -> Path:
    """Return SwayDeck's per-user runtime state directory."""

    runtime_root = Path(
        os.environ.get(
            "XDG_RUNTIME_DIR",
            "/tmp",
        )
    )

    return runtime_root / f"swaydeck-{os.getuid()}"


def default_pid_file() -> Path:
    """Return the default wl-mirror PID-file path."""

    return default_state_dir() / "wl-mirror.pids"


def _read_pids(
    pid_file: Path,
) -> tuple[int, ...]:
    """Read valid integer PIDs from a SwayDeck PID file."""

    try:
        content = pid_file.read_text()
    except FileNotFoundError:
        return ()
    except OSError:
        return ()

    pids: list[int] = []

    for line in content.splitlines():
        value = line.strip()

        if not value.isdigit():
            continue

        pid = int(value)

        if pid > 0:
            pids.append(pid)

    return tuple(pids)


def _pid_is_wl_mirror(
    pid: int,
) -> bool:
    """Verify that a live PID belongs to wl-mirror."""

    try:
        os.kill(
            pid,
            0,
        )
    except OSError:
        return False

    try:
        cmdline = Path(
            f"/proc/{pid}/cmdline"
        ).read_bytes()
    except OSError:
        return False

    return b"wl-mirror" in cmdline


def mirror_alive(
    pid_file: Path | None = None,
) -> bool:
    """Return True when a recorded wl-mirror process is alive."""

    path = (
        pid_file
        if pid_file is not None
        else default_pid_file()
    )

    return any(
        _pid_is_wl_mirror(pid)
        for pid in _read_pids(path)
    )


def stop_mirror(
    pid_file: Path | None = None,
) -> None:
    """Stop only verified wl-mirror processes from the PID file."""

    path = (
        pid_file
        if pid_file is not None
        else default_pid_file()
    )

    for pid in _read_pids(path):
        if not _pid_is_wl_mirror(pid):
            continue

        try:
            os.kill(
                pid,
                signal.SIGTERM,
            )
        except ProcessLookupError:
            pass
        except PermissionError:
            # Do not escalate or attempt to kill an unmanageable PID.
            pass

    try:
        path.unlink(
            missing_ok=True
        )
    except OSError as exc:
        raise MirrorError(
            f"unable to remove mirror PID file: {path}"
        ) from exc


def _cleanup_started_processes(
    processes: Iterable[subprocess.Popen[bytes]],
) -> None:
    """Terminate processes started by the current failed operation."""

    for process in processes:
        try:
            if process.poll() is None:
                process.terminate()
        except OSError:
            pass

def require_wl_mirror() -> str:
    """Return the wl-mirror executable or raise a clear error."""

    binary = shutil.which(
        "wl-mirror"
    )

    if binary is None:
        raise MirrorError(
            "wl-mirror is not installed or not available in PATH"
        )

    return binary

def start_mirror(
    primary: str,
    externals: Iterable[str],
    *,
    pid_file: Path | None = None,
    verify_delay: float = 0.2,
) -> tuple[int, ...]:
    """Start wl-mirror for one or more external outputs.

    Display outputs must already be enabled before this function is
    called. That orchestration belongs to the workflow layer.
    """

    targets = tuple(externals)

    if not targets:
        raise MirrorError(
            "no external outputs available for mirroring"
        )

    if verify_delay < 0:
        raise ValueError(
            "verify_delay must not be negative"
        )

    binary = require_wl_mirror()

    path = (
        pid_file
        if pid_file is not None
        else default_pid_file()
    )

    stop_mirror(path)

    try:
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
    except OSError as exc:
        raise MirrorError(
            f"unable to create mirror state directory: {path.parent}"
        ) from exc

    processes: list[subprocess.Popen[bytes]] = []

    try:
        for output in targets:
            process = subprocess.Popen(
                [
                    binary,
                    "--fullscreen-output",
                    output,
                    "--fullscreen",
                    primary,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            processes.append(
                process
            )

        path.write_text(
            "".join(
                f"{process.pid}\n"
                for process in processes
            )
        )

    except OSError as exc:
        _cleanup_started_processes(
            processes
        )

        path.unlink(
            missing_ok=True
        )

        raise MirrorError(
            "unable to start wl-mirror"
        ) from exc

    if verify_delay:
        time.sleep(
            verify_delay
        )

    if not mirror_alive(path):
        _cleanup_started_processes(
            processes
        )

        path.unlink(
            missing_ok=True
        )

        raise MirrorError(
            "wl-mirror failed to remain running"
        )

    return tuple(
        process.pid
        for process in processes
    )
