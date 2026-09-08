"""Core Python components for SwayDeck."""

from .models import Output, Rect
from .topology import (
    projection_mode,
    select_primary,
    two_layout_direction,
)

__all__ = [
    "Output",
    "Rect",
    "projection_mode",
    "select_primary",
    "two_layout_direction",
]
