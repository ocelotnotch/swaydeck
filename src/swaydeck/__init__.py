"""Core Python components for SwayDeck."""

from .models import Output, Rect
from .sway import (
    SwayCommandError,
    SwayError,
    SwayProtocolError,
    get_outputs,
)
from .topology import (
    projection_mode,
    select_primary,
    two_layout_direction,
)

__all__ = [
    "Output",
    "Rect",
    "SwayCommandError",
    "SwayError",
    "SwayProtocolError",
    "get_outputs",
    "projection_mode",
    "select_primary",
    "two_layout_direction",
]
