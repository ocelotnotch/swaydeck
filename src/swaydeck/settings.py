"""Scale and orientation workflows for SwayDeck."""

from __future__ import annotations

import time

from .mirror import mirror_alive
from .sway import (
    get_outputs,
    scale_output,
    transform_output,
)
from .topology import (
    select_primary,
    two_layout_direction,
)
from .workflows import arrange_displays


DEFAULT_SETTLE_SECONDS = 0.15

VALID_TRANSFORMS = {
    "normal",
    "90",
    "180",
    "270",
}


class SettingsError(RuntimeError):
    """Raised when display settings cannot be changed safely."""


def transform_label(
    transform: str,
) -> str:
    labels = {
        "normal": "Landscape",
        "90": "Portrait",
        "180": "Landscape flipped",
        "270": "Portrait flipped",
    }

    return labels.get(
        transform,
        transform,
    )


def _require_active_target(
    target: str,
) -> None:
    outputs = get_outputs()

    exists = any(
        output.name == target
        and output.active
        for output in outputs
    )

    if not exists:
        raise SettingsError(
            f"active output not found: {target}"
        )


def _two_monitor_context(
    primary_override: str | None = None,
) -> tuple[str, str, str] | None:
    outputs = get_outputs()

    active = [
        output
        for output in outputs
        if output.active
    ]

    if len(active) != 2:
        return None

    primary = select_primary(
        outputs,
        primary_override,
    )

    if primary is None:
        return None

    by_name = {
        output.name: output
        for output in active
    }

    if primary not in by_name:
        return None

    external = next(
        (
            output
            for output in active
            if output.name != primary
        ),
        None,
    )

    if external is None:
        return None

    direction = two_layout_direction(
        by_name[primary],
        external,
    )

    return (
        primary,
        external.name,
        direction,
    )


def apply_scale(
    target: str,
    scale: float,
    *,
    primary_override: str | None = None,
    settle_seconds: float = DEFAULT_SETTLE_SECONDS,
) -> None:
    if mirror_alive():
        raise SettingsError(
            "switch out of Duplicate before changing display settings"
        )

    if scale <= 0:
        raise ValueError(
            "scale must be positive"
        )

    if settle_seconds < 0:
        raise ValueError(
            "settle_seconds must not be negative"
        )

    _require_active_target(
        target
    )

    context = _two_monitor_context(
        primary_override
    )

    scale_output(
        target,
        scale,
    )

    if settle_seconds:
        time.sleep(
            settle_seconds
        )

    if context is not None:
        primary, external, direction = context

        arrange_displays(
            external,
            primary,
            direction,
        )


def apply_orientation(
    target: str,
    transform: str,
    *,
    primary_override: str | None = None,
    settle_seconds: float = DEFAULT_SETTLE_SECONDS,
) -> None:
    if transform not in VALID_TRANSFORMS:
        raise ValueError(
            f"unsupported transform: {transform}"
        )

    if mirror_alive():
        raise SettingsError(
            "switch out of Duplicate before changing display settings"
        )

    if settle_seconds < 0:
        raise ValueError(
            "settle_seconds must not be negative"
        )

    _require_active_target(
        target
    )

    context = _two_monitor_context(
        primary_override
    )

    transform_output(
        target,
        transform,
    )

    if settle_seconds:
        time.sleep(
            settle_seconds
        )

    if context is not None:
        primary, external, direction = context

        arrange_displays(
            external,
            primary,
            direction,
        )
