"""Read-only adapter for communicating with Sway."""

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


def _parse_outputs(payload: str) -> list[Output]:
    """Parse and validate the JSON returned by ``swaymsg get_outputs``."""

    try:
        data: Any = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise SwayProtocolError("Sway returned invalid JSON") from exc

    if not isinstance(data, list):
        raise SwayProtocolError("Sway output response must be a JSON array")

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
            outputs.append(Output.from_sway(item))
        except (TypeError, ValueError, KeyError) as exc:
            raise SwayProtocolError(
                f"Unable to parse Sway output at index {index}"
            ) from exc

    return outputs


def get_outputs(*, timeout: float = 5.0) -> list[Output]:
    """Read the current output state from Sway.

    This operation is read-only. It does not change any display state.
    """

    try:
        result = subprocess.run(
            ["swaymsg", "-r", "-t", "get_outputs"],
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
        detail = result.stderr.strip() or "unknown swaymsg error"

        raise SwayCommandError(
            f"swaymsg get_outputs failed: {detail}"
        )

    return _parse_outputs(result.stdout)
