"""Pure display-operation planning for SwayDeck workflows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .models import Output


@dataclass(frozen=True, slots=True)
class EnableOp:
    output: str


@dataclass(frozen=True, slots=True)
class DisableOp:
    output: str


@dataclass(frozen=True, slots=True)
class PositionOp:
    output: str
    x: int
    y: int


OutputOperation = EnableOp | DisableOp | PositionOp


def _require_output(
    outputs: tuple[Output, ...],
    name: str,
    *,
    role: str,
) -> None:
    if not any(output.name == name for output in outputs):
        raise ValueError(
            f"{role} output not found: {name}"
        )


def plan_pc_only(
    outputs: Iterable[Output],
    primary: str,
) -> list[OutputOperation]:
    """Plan the existing SwayDeck PC-screen-only workflow.

    The primary output is enabled and moved to the origin before all
    other reported outputs are disabled.
    """

    items = tuple(outputs)

    _require_output(
        items,
        primary,
        role="primary",
    )

    operations: list[OutputOperation] = [
        EnableOp(primary),
        PositionOp(primary, 0, 0),
    ]

    operations.extend(
        DisableOp(output.name)
        for output in items
        if output.name != primary
    )

    return operations


def plan_second_only(
    outputs: Iterable[Output],
    primary: str,
    target: str,
) -> list[OutputOperation]:
    """Plan the existing SwayDeck second-screen-only workflow.

    The external destination is enabled before any other output is
    disabled. The primary output is deliberately disabled last.
    """

    items = tuple(outputs)

    _require_output(
        items,
        primary,
        role="primary",
    )
    _require_output(
        items,
        target,
        role="target",
    )

    if target == primary:
        raise ValueError(
            "target output must differ from primary output"
        )

    operations: list[OutputOperation] = [
        EnableOp(target),
        PositionOp(target, 0, 0),
    ]

    operations.extend(
        DisableOp(output.name)
        for output in items
        if output.name not in {primary, target}
    )

    # Safety invariant inherited from the Bash implementation:
    # never disable the primary before the destination is enabled.
    operations.append(
        DisableOp(primary)
    )

    return operations


VALID_DIRECTIONS = {
    "Right",
    "Left",
    "Above",
    "Below",
}


def _require_geometry(
    output: Output,
) -> None:
    if output.rect is None:
        raise ValueError(
            f"output has no geometry: {output.name}"
        )


def _require_direction(
    direction: str,
) -> None:
    if direction not in VALID_DIRECTIONS:
        raise ValueError(
            f"unsupported direction: {direction}"
        )


def plan_arrange_two(
    anchor: Output,
    target: Output,
    direction: str,
) -> list[PositionOp]:
    """Plan absolute positioning for a two-display layout."""

    if anchor.name == target.name:
        raise ValueError(
            "target output must differ from anchor output"
        )

    _require_geometry(anchor)
    _require_geometry(target)
    _require_direction(direction)

    anchor_rect = anchor.rect
    target_rect = target.rect

    assert anchor_rect is not None
    assert target_rect is not None

    if direction == "Right":
        return [
            PositionOp(anchor.name, 0, 0),
            PositionOp(
                target.name,
                anchor_rect.width,
                0,
            ),
        ]

    if direction == "Left":
        return [
            PositionOp(target.name, 0, 0),
            PositionOp(
                anchor.name,
                target_rect.width,
                0,
            ),
        ]

    if direction == "Above":
        return [
            PositionOp(target.name, 0, 0),
            PositionOp(
                anchor.name,
                0,
                target_rect.height,
            ),
        ]

    return [
        PositionOp(anchor.name, 0, 0),
        PositionOp(
            target.name,
            0,
            anchor_rect.height,
        ),
    ]


def plan_arrange_multi(
    outputs: Iterable[Output],
    target: str,
    anchor: str,
    direction: str,
) -> list[PositionOp]:
    """Move one active display relative to another.

    If the operation would produce negative coordinates, the complete
    active-display canvas is shifted back into non-negative space.
    """

    items = tuple(
        output
        for output in outputs
        if output.active
    )

    _require_direction(direction)

    if target == anchor:
        raise ValueError(
            "target output must differ from anchor output"
        )

    by_name = {
        output.name: output
        for output in items
    }

    if target not in by_name:
        raise ValueError(
            f"active target output not found: {target}"
        )

    if anchor not in by_name:
        raise ValueError(
            f"active anchor output not found: {anchor}"
        )

    for output in items:
        _require_geometry(output)

    target_output = by_name[target]
    anchor_output = by_name[anchor]

    assert target_output.rect is not None
    assert anchor_output.rect is not None

    positions = {
        output.name: [
            output.rect.x,
            output.rect.y,
        ]
        for output in items
        if output.rect is not None
    }

    target_rect = target_output.rect
    anchor_rect = anchor_output.rect

    if direction == "Right":
        positions[target] = [
            anchor_rect.x + anchor_rect.width,
            anchor_rect.y,
        ]

    elif direction == "Left":
        positions[target] = [
            anchor_rect.x - target_rect.width,
            anchor_rect.y,
        ]

    elif direction == "Above":
        positions[target] = [
            anchor_rect.x,
            anchor_rect.y - target_rect.height,
        ]

    else:
        positions[target] = [
            anchor_rect.x,
            anchor_rect.y + anchor_rect.height,
        ]

    min_x = min(
        position[0]
        for position in positions.values()
    )
    min_y = min(
        position[1]
        for position in positions.values()
    )

    shift_x = -min_x if min_x < 0 else 0
    shift_y = -min_y if min_y < 0 else 0

    return [
        PositionOp(
            output.name,
            positions[output.name][0] + shift_x,
            positions[output.name][1] + shift_y,
        )
        for output in items
    ]


def plan_right_chain(
    outputs: Iterable[Output],
    primary: str,
) -> list[PositionOp]:
    """Arrange already-enabled outputs in a deterministic right chain.

    This planner must be called only after all desired outputs have
    been enabled and their current geometry has been read again.
    """

    items = tuple(outputs)

    if not items:
        raise ValueError(
            "no outputs available"
        )

    by_name = {
        output.name: output
        for output in items
    }

    if primary not in by_name:
        raise ValueError(
            f"primary output not found: {primary}"
        )

    for output in items:
        if not output.active:
            raise ValueError(
                f"output must be active before right-chain planning: "
                f"{output.name}"
            )

        _require_geometry(output)

    ordered = [
        by_name[primary],
        *(
            output
            for output in items
            if output.name != primary
        ),
    ]

    operations: list[PositionOp] = []
    x = 0

    for output in ordered:
        assert output.rect is not None

        operations.append(
            PositionOp(
                output.name,
                x,
                0,
            )
        )

        x += output.rect.width

    return operations
