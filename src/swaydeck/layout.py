"""Persistent Sway layout serialization, validation and rollback."""

from __future__ import annotations

from datetime import datetime
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
from typing import Any

from .mirror import mirror_alive


OUTPUT_NAME_RE = re.compile(
    r"^[A-Za-z0-9._:-]+$"
)


class LayoutError(RuntimeError):
    """Raised when a layout cannot be persisted safely."""


def default_layout_file() -> Path:
    config_home = Path(
        os.environ.get(
            "XDG_CONFIG_HOME",
            str(Path.home() / ".config"),
        )
    )

    return (
        config_home
        / "sway"
        / "config.d"
        / "90-swaydeck-layout.conf"
    )


def default_backup_dir() -> Path:
    config_home = Path(
        os.environ.get(
            "XDG_CONFIG_HOME",
            str(Path.home() / ".config"),
        )
    )

    return (
        config_home
        / "swaydeck-backups"
    )


def _read_raw_outputs(
    timeout: float = 2.0,
) -> list[dict[str, Any]]:
    try:
        result = subprocess.run(
            [
                "swaymsg",
                "-r",
                "-t",
                "get_outputs",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

    except (
        FileNotFoundError,
        subprocess.TimeoutExpired,
    ) as exc:
        raise LayoutError(
            "unable to read current Sway outputs"
        ) from exc

    if result.returncode != 0:
        raise LayoutError(
            "unable to read current Sway outputs"
        )

    try:
        data = json.loads(
            result.stdout
        )
    except json.JSONDecodeError as exc:
        raise LayoutError(
            "invalid output data returned by Sway"
        ) from exc

    if not isinstance(
        data,
        list,
    ):
        raise LayoutError(
            "invalid output data returned by Sway"
        )

    if not all(
        isinstance(item, dict)
        for item in data
    ):
        raise LayoutError(
            "invalid output data returned by Sway"
        )

    return data


def layout_signature(
    outputs: list[dict[str, Any]],
) -> tuple[tuple[Any, ...], ...]:
    signature: list[tuple[Any, ...]] = []

    for output in outputs:
        name = output.get(
            "name"
        )

        active = bool(
            output.get(
                "active",
                False,
            )
        )

        if active:
            mode = (
                output.get("current_mode")
                or {}
            )

            rect = (
                output.get("rect")
                or {}
            )

            state: Any = (
                mode.get("width"),
                mode.get("height"),
                mode.get("refresh"),
                output.get("scale"),
                output.get(
                    "transform",
                    "normal",
                ),
                rect.get("x"),
                rect.get("y"),
            )
        else:
            state = None

        signature.append(
            (
                name,
                active,
                state,
            )
        )

    return tuple(
        sorted(
            signature,
            key=lambda item: str(
                item[0]
            ),
        )
    )


def _refresh_hz(
    refresh_millihz: int | float,
) -> str:
    value = (
        float(refresh_millihz)
        / 1000.0
    )

    return (
        f"{value:.3f}"
        .rstrip("0")
        .rstrip(".")
    )


def generate_layout_config(
    outputs: list[dict[str, Any]],
) -> str:
    if not outputs:
        raise LayoutError(
            "no outputs detected"
        )

    lines = [
        "# Managed by SwayDeck.",
        "# Manual edits may be overwritten.",
        "",
    ]

    for output in outputs:
        name = output.get(
            "name"
        )

        if (
            not isinstance(name, str)
            or OUTPUT_NAME_RE.fullmatch(name) is None
        ):
            raise LayoutError(
                "unsafe output name"
            )

        if not output.get(
            "active",
            False,
        ):
            lines.append(
                f"output {name} disable"
            )
            continue

        mode = output.get(
            "current_mode"
        )

        rect = output.get(
            "rect"
        )

        scale = output.get(
            "scale"
        )

        transform = output.get(
            "transform",
            "normal",
        )

        if (
            not isinstance(mode, dict)
            or not isinstance(rect, dict)
            or scale is None
        ):
            raise LayoutError(
                "active output is missing persistent geometry"
            )

        width = mode.get(
            "width"
        )

        height = mode.get(
            "height"
        )

        refresh = mode.get(
            "refresh"
        )

        x = rect.get(
            "x"
        )

        y = rect.get(
            "y"
        )

        if any(
            value is None
            for value in (
                width,
                height,
                refresh,
                x,
                y,
            )
        ):
            raise LayoutError(
                "active output is missing persistent geometry"
            )

        lines.append(
            " ".join(
                [
                    "output",
                    name,
                    "mode",
                    (
                        f"{width}x{height}"
                        f"@{_refresh_hz(refresh)}Hz"
                    ),
                    "scale",
                    str(scale),
                    "transform",
                    str(transform),
                    "position",
                    str(x),
                    str(y),
                ]
            )
        )

    return (
        "\n".join(lines)
        + "\n"
    )


def _validate_candidate(
    candidate: Path,
) -> None:
    sway = shutil.which(
        "sway"
    )

    if sway is None:
        return

    result = subprocess.run(
        [
            sway,
            "-C",
            "-c",
            str(candidate),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise LayoutError(
            "generated Sway layout failed syntax validation"
        )


def _reload_sway() -> None:
    result = subprocess.run(
        [
            "swaymsg",
            "reload",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise LayoutError(
            "Sway reload failed"
        )


def _restore_layout(
    destination: Path,
    previous: bytes | None,
) -> None:
    if previous is None:
        destination.unlink(
            missing_ok=True
        )
        return

    temporary = destination.with_name(
        destination.name
        + ".restore"
    )

    temporary.write_bytes(
        previous
    )

    os.chmod(
        temporary,
        0o644,
    )

    os.replace(
        temporary,
        destination,
    )


def save_current_layout(
    *,
    layout_file: Path | None = None,
    backup_dir: Path | None = None,
    verify_delay: float = 0.5,
) -> Path:
    if verify_delay < 0:
        raise ValueError(
            "verify_delay must not be negative"
        )

    if mirror_alive():
        raise LayoutError(
            "Duplicate mode cannot be persisted with wl-mirror"
        )

    destination = (
        layout_file
        if layout_file is not None
        else default_layout_file()
    )

    backups = (
        backup_dir
        if backup_dir is not None
        else default_backup_dir()
    )

    before = _read_raw_outputs()

    if not before:
        raise LayoutError(
            "no outputs detected"
        )

    if not any(
        output.get(
            "active",
            False,
        )
        for output in before
    ):
        raise LayoutError(
            "no active outputs detected"
        )

    before_signature = layout_signature(
        before
    )

    content = generate_layout_config(
        before
    )

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    backups.mkdir(
        parents=True,
        exist_ok=True,
    )

    previous = (
        destination.read_bytes()
        if destination.exists()
        else None
    )

    if previous is not None:
        stamp = datetime.now().strftime(
            "%Y%m%d-%H%M%S"
        )

        backup = (
            backups
            / (
                f"layout-{stamp}-"
                f"{os.getpid()}.conf"
            )
        )

        shutil.copy2(
            destination,
            backup,
        )

    candidate = destination.with_name(
        destination.name
        + ".candidate"
    )

    replacement = destination.with_name(
        destination.name
        + ".new"
    )

    try:
        candidate.write_text(
            content
        )

        _validate_candidate(
            candidate
        )

        replacement.write_text(
            content
        )

        os.chmod(
            replacement,
            0o644,
        )

        os.replace(
            replacement,
            destination,
        )

        try:
            _reload_sway()

            if verify_delay:
                time.sleep(
                    verify_delay
                )

            after = _read_raw_outputs()

            if (
                layout_signature(after)
                != before_signature
            ):
                raise LayoutError(
                    "reload changed the display state"
                )

        except LayoutError as exc:
            _restore_layout(
                destination,
                previous,
            )

            try:
                _reload_sway()
            except LayoutError:
                pass

            raise LayoutError(
                f"{exc}; previous layout restored"
            ) from exc

        return destination

    finally:
        candidate.unlink(
            missing_ok=True
        )

        replacement.unlink(
            missing_ok=True
        )
