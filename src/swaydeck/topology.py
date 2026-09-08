"""Pure display-topology logic extracted from the Bash implementation."""

from __future__ import annotations

from collections.abc import Iterable

from .models import Output


def select_primary(
    outputs: Iterable[Output],
    override: str | None = None,
) -> str | None:
    """Choose the primary display using SwayDeck's existing policy."""

    items = tuple(outputs)

    if override and any(output.name == override for output in items):
        return override

    for output in items:
        if output.name.startswith("eDP-"):
            return output.name

    for output in items:
        if output.active:
            return output.name

    return items[0].name if items else None


def projection_mode(
    outputs: Iterable[Output],
    primary: str,
    *,
    mirror_active: bool = False,
) -> str:
    """Return SwayDeck's current projection-mode label."""

    items = tuple(outputs)

    if mirror_active:
        return "Duplicate"

    active_count = sum(output.active for output in items)

    primary_active = any(
        output.name == primary and output.active
        for output in items
    )

    if active_count == 1 and primary_active:
        return "PC screen only"

    if active_count == 1 and not primary_active:
        return "Second screen only"

    if active_count >= 2:
        return "Extend"

    return "Unknown"


def two_layout_direction(
    primary: Output,
    target: Output,
) -> str:
    """Determine target position relative to the primary output."""

    if primary.rect is None or target.rect is None:
        raise ValueError("both outputs must have geometry")

    p = primary.rect
    t = target.rect

    if t.x >= p.x + p.width:
        return "Right"

    if p.x >= t.x + t.width:
        return "Left"

    if t.y >= p.y + p.height:
        return "Below"

    if p.y >= t.y + t.height:
        return "Above"

    # Offset/overlapping layouts use the dominant center-to-center axis.
    primary_cx = p.x + p.width // 2
    primary_cy = p.y + p.height // 2

    target_cx = t.x + t.width // 2
    target_cy = t.y + t.height // 2

    dx = target_cx - primary_cx
    dy = target_cy - primary_cy

    if abs(dx) >= abs(dy):
        return "Right" if dx >= 0 else "Left"

    return "Below" if dy >= 0 else "Above"
