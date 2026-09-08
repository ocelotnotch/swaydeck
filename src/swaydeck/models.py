"""Typed models representing Sway output state."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class Rect:
    x: int
    y: int
    width: int
    height: int


@dataclass(frozen=True, slots=True)
class Output:
    name: str
    active: bool
    rect: Rect | None = None
    scale: float | None = None
    transform: str = "normal"

    @classmethod
    def from_sway(cls, data: dict[str, Any]) -> "Output":
        rect_data = data.get("rect")
        rect = None

        if isinstance(rect_data, dict) and all(
            key in rect_data
            for key in ("x", "y", "width", "height")
        ):
            rect = Rect(
                x=int(rect_data["x"]),
                y=int(rect_data["y"]),
                width=int(rect_data["width"]),
                height=int(rect_data["height"]),
            )

        scale = data.get("scale")

        return cls(
            name=str(data["name"]),
            active=bool(data.get("active")),
            rect=rect,
            scale=float(scale) if scale is not None else None,
            transform=str(data.get("transform") or "normal"),
        )
