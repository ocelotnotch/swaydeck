"""Execution boundary for planned SwayDeck display operations."""

from __future__ import annotations

from collections.abc import Iterable

from .plans import (
    DisableOp,
    EnableOp,
    OutputOperation,
    PositionOp,
)
from .sway import (
    disable_output,
    enable_output,
    position_output,
)


def execute_operation(
    operation: OutputOperation,
) -> None:
    """Execute one planned display operation."""

    if isinstance(operation, EnableOp):
        enable_output(operation.output)
        return

    if isinstance(operation, DisableOp):
        disable_output(operation.output)
        return

    if isinstance(operation, PositionOp):
        position_output(
            operation.output,
            operation.x,
            operation.y,
        )
        return

    raise TypeError(
        f"unsupported output operation: {type(operation).__name__}"
    )


def execute_operations(
    operations: Iterable[OutputOperation],
) -> None:
    """Execute operations sequentially in planner-defined order."""

    for operation in operations:
        execute_operation(operation)
