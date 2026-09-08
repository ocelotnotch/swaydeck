"""Adapter for communicating with Sway."""

from __future__ import annotations

import json
import subprocess
from typing import Any

from .models import Output


class SwayError(RuntimeError):
    """Base exception for Sway communication failures."""


class SwayCommandError(SwayError):
    """Raised when swaymsg cannot successfully execute."""


class SwayProtocolError(SwayError):
    """Raised when Sway returns unexpected or invalid data."""


def _run(
    args: list[str],
    *,
    timeout: float = 5.0,
) -> subprocess.CompletedProcess[str]:
    """Execute swaymsg and normalize infrastructure failures."""

    command = ["swaymsg", *args]

    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        raise SwayCommandError(
            "swaymsg is not installed or not available in PATH"
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise SwayCommandError(
            f"swaymsg timed out after {timeout:g} seconds"
        ) from exc
    except OSError as exc:
        raise SwayCommandError(
            f"Unable to execute swaymsg: {exc}"
        ) from exc

    if result.returncode != 0:
        detail = (
            result.stderr.strip()
            or result.stdout.strip()
            or "unknown swaymsg error"
        )

        raise SwayCommandError(
            f"swaymsg failed: {detail}"
        )

    return result


def _parse_outputs(payload: str) -> list[Output]:
    """Parse and validate ``swaymsg get_outputs`` JSON."""

    try:
        data: Any = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise SwayProtocolError(
            "Sway returned invalid JSON"
        ) from exc

    if not isinstance(data, list):
        raise SwayProtocolError(
            "Sway output response must be a JSON array"
        )

    outputs: list[Output] = []

    for index, item in enumerate(data):
        if not isinstance(item, dict):
            raise SwayProtocolError(
                f"Sway output at index {index} is not an object"
            )

        if "name" not in item:
            raise SwayProtocolError(
                f"Sway output at index {index} has no name"
            )

        try:
            outputs.append(
                Output.from_sway(item)
            )
        except (TypeError, ValueError, KeyError) as exc:
            raise SwayProtocolError(
                f"Unable to parse Sway output at index {index}"
            ) from exc

    return outputs


def get_outputs(
    *,
    timeout: float = 5.0,
) -> list[Output]:
    """Read the current output state from Sway."""

    result = _run(
        ["-r", "-t", "get_outputs"],
        timeout=timeout,
    )

    return _parse_outputs(result.stdout)


def run_sway_command(
    command: str,
    *,
    timeout: float = 5.0,
) -> None:
    """Execute one Sway command."""

    if not command.strip():
        raise ValueError("Sway command must not be empty")

    _run(
        ["-q", "--", command],
        timeout=timeout,
    )


def enable_output(
    output: str,
    *,
    timeout: float = 5.0,
) -> None:
    """Enable an output."""

    run_sway_command(
        f"output {output} enable",
        timeout=timeout,
    )


def disable_output(
    output: str,
    *,
    timeout: float = 5.0,
) -> None:
    """Disable an output."""

    run_sway_command(
        f"output {output} disable",
        timeout=timeout,
    )


def position_output(
    output: str,
    x: int,
    y: int,
    *,
    timeout: float = 5.0,
) -> None:
    """Place an output at logical coordinates."""

    run_sway_command(
        f"output {output} position {x} {y}",
        timeout=timeout,
    )


def scale_output(
    output: str,
    scale: float,
    *,
    timeout: float = 5.0,
) -> None:
    """Set output scale."""

    if scale <= 0:
        raise ValueError("scale must be greater than zero")

    run_sway_command(
        f"output {output} scale {scale:g}",
        timeout=timeout,
    )


def transform_output(
    output: str,
    transform: str,
    *,
    timeout: float = 5.0,
) -> None:
    """Set output orientation transform."""

    valid = {
        "normal",
        "90",
        "180",
        "270",
        "flipped",
        "flipped-90",
        "flipped-180",
        "flipped-270",
    }

    if transform not in valid:
        raise ValueError(
            f"unsupported transform: {transform}"
        )

    run_sway_command(
        f"output {output} transform {transform}",
        timeout=timeout,
    )
