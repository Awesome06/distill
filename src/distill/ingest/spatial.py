"""Spatial coordinate sorting to preserve left-to-right reading order."""

from __future__ import annotations

from typing import Any, Protocol


class PositionedShape(Protocol):
    """Protocol for any shape with bounding box properties."""

    top: int
    left: int
    width: int
    height: int


def sort_shapes_spatially(
    shapes: list[Any],
    line_threshold: int = 150_000,
) -> list[Any]:
    """Sort slide shapes by geometric coordinates to eliminate z-order text scrambling.

    In OpenXML/PowerPoint, shapes are ordered by creation timestamp or z-order index.
    A side-by-side comparison slide often stores the right column before the left column.
    This function groups shapes into horizontal line bands using `top // line_threshold`,
    then sorts shapes left-to-right within each line band.

    Args:
        shapes: List of python-pptx shape objects.
        line_threshold: Coordinate threshold in EMUs (English Metric Units) to group shapes
            into the same horizontal row. Default is 150,000 EMUs (~0.16 inches).

    Returns:
        Spatially ordered list of shapes.
    """

    def shape_sort_key(s: Any) -> tuple[int, int]:
        top = getattr(s, "top", 0) or 0
        left = getattr(s, "left", 0) or 0
        # Compute row band bucket, then order by horizontal position
        row_band = top // line_threshold
        return (row_band, left)

    return sorted(shapes, key=shape_sort_key)
