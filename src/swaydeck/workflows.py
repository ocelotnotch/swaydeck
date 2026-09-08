"""High-level display workflows for SwayDeck."""

from __future__ import annotations

import time

from .executor import execute_operations
from .models import Output
from .mirror import (
    require_wl_mirror,
    start_mirror,
    stop_mirror,
)
from .plans import (
    EnableOp,
    OutputOperation,
    plan_arrange_multi,
    plan_arrange_two,
    plan_pc_only,
    plan_right_chain,
    plan_second_only,
)
from .sway import get_outputs
from .topology import select_primary


DEFAULT_SETTLE_SECONDS = 0.15


class WorkflowError(RuntimeError):
    """Raised when a display workflow cannot be planned safely."""


def _resolve_primary(
    outputs: list[Output],
    override: str | None = None,
) -> str:
    primary = select_primary(
        outputs,
        override,
    )

    if primary is None:
        raise WorkflowError(
            "no Sway outputs detected"
        )

    return primary


def apply_pc_only(
    *,
    primary_override: str | None = None,
) -> list[OutputOperation]:
    """Apply the PC-screen-only workflow."""

    outputs = get_outputs()

    primary = _resolve_primary(
        outputs,
        primary_override,
    )

    operations = plan_pc_only(
        outputs,
        primary,
    )

    execute_operations(
        operations
    )

    return operations


def apply_second_only(
    target: str,
    *,
    primary_override: str | None = None,
) -> list[OutputOperation]:
    """Apply the second-screen-only workflow."""

    outputs = get_outputs()

    primary = _resolve_primary(
        outputs,
        primary_override,
    )

    operations = plan_second_only(
        outputs,
        primary,
        target,
    )

    execute_operations(
        operations
    )

    return operations


def apply_extend_right(
    *,
    primary_override: str | None = None,
    settle_seconds: float = DEFAULT_SETTLE_SECONDS,
) -> list[OutputOperation]:
    """Enable reported outputs and arrange them in a rightward chain.

    Geometry is intentionally read again after enabling the outputs.
    Sway may report different logical dimensions once an output becomes
    active.
    """

    if settle_seconds < 0:
        raise ValueError(
            "settle_seconds must not be negative"
        )

    outputs = get_outputs()

    primary = _resolve_primary(
        outputs,
        primary_override,
    )

    enable_operations: list[OutputOperation] = [
        EnableOp(output.name)
        for output in outputs
    ]

    execute_operations(
        enable_operations
    )

    if settle_seconds:
        time.sleep(
            settle_seconds
        )

    refreshed = get_outputs()

    position_operations = plan_right_chain(
        refreshed,
        primary,
    )

    execute_operations(
        position_operations
    )

    return [
        *enable_operations,
        *position_operations,
    ]


def arrange_displays(
    target: str,
    anchor: str,
    direction: str,
) -> list[OutputOperation]:
    """Arrange one active output relative to another."""

    outputs = get_outputs()

    active = [
        output
        for output in outputs
        if output.active
    ]

    if len(active) < 2:
        raise WorkflowError(
            "at least two active outputs are required"
        )

    by_name = {
        output.name: output
        for output in active
    }

    if target not in by_name:
        raise WorkflowError(
            f"active target output not found: {target}"
        )

    if anchor not in by_name:
        raise WorkflowError(
            f"active anchor output not found: {anchor}"
        )

    if len(active) == 2:
        operations: list[OutputOperation] = (
            plan_arrange_two(
                by_name[anchor],
                by_name[target],
                direction,
            )
        )

    else:
        operations = plan_arrange_multi(
            active,
            target,
            anchor,
            direction,
        )

    execute_operations(
        operations
    )

    return operations

def apply_duplicate(
    *,
    primary_override: str | None = None,
    settle_seconds: float = DEFAULT_SETTLE_SECONDS,
    verify_delay: float = 0.2,
) -> tuple[int, ...]:
    """Mirror the primary output onto all external outputs."""

    stop_mirror()

    # Do not mutate display topology if wl-mirror is unavailable.
    require_wl_mirror()

    outputs = get_outputs()

    primary = _resolve_primary(
        outputs,
        primary_override,
    )

    externals = tuple(
        output.name
        for output in outputs
        if output.name != primary
    )

    if not externals:
        raise WorkflowError(
            "no external outputs detected"
        )

    apply_extend_right(
        primary_override=primary,
        settle_seconds=settle_seconds,
    )

    return start_mirror(
        primary,
        externals,
        verify_delay=verify_delay,
    )
