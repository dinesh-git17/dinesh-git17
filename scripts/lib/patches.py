"""Patch catalogue: maps source fields to SVG markers and element attributes.

The runner walks ``catalogue()`` and applies each entry to the SVG via
``svg_markers.patch_marker`` (for text content bounded by comment markers)
or ``svg_markers.patch_element_attribute`` (for ring dasharrays and bar widths).
"""

import math
from dataclasses import dataclass
from typing import Callable, Literal

GRADE_RING_RADIUS: int = 38
STREAK_RING_RADIUS: int = 46
LANG_BAR_TRACK: int = 145
LANG_BAR_CAP: int = 142
LANG_BAR_FLOOR: int = 2


@dataclass(frozen=True)
class PatchEntry:
    """One row in the patch catalogue."""

    source: str
    target_kind: Literal["marker", "attribute"]
    target_id: str
    attribute_name: str | None
    value_fn: Callable[[dict], str]


def bar_scale(*, top_seconds: float, my_seconds: float) -> int:
    """Return the bar width in pixels for a single language row.

    The top row lands at ``LANG_BAR_CAP`` (the visual cap, slightly inset
    from ``LANG_BAR_TRACK``). Other rows scale proportionally. A floor of
    2 px keeps tail entries visible.
    """
    if top_seconds <= 0:
        return LANG_BAR_FLOOR
    raw: float = LANG_BAR_CAP * my_seconds / top_seconds
    return max(LANG_BAR_FLOOR, round(raw))


def ring_circumference(radius: int) -> int:
    """Return the integer circumference for a ring of the given radius."""
    return round(2 * math.pi * radius)


def grade_dasharray(*, percentile: float) -> str:
    """Return the ``stroke-dasharray`` value for the grade ring.

    Lower percentile (better rank) produces a longer arc.
    """
    circ: int = ring_circumference(GRADE_RING_RADIUS)
    arc: int = round(circ * (100.0 - percentile) / 100.0)
    arc = min(circ, max(0, arc))
    return f"{arc} {circ}"


def streak_dasharray(*, current: int, longest: int) -> str:
    """Return the ``stroke-dasharray`` value for the streak ring.

    Full ring when current ties the record. Zero arc when longest is zero.
    """
    circ: int = ring_circumference(STREAK_RING_RADIUS)
    if longest <= 0:
        return f"0 {circ}"
    arc: int = round(circ * current / longest)
    arc = min(circ, max(0, arc))
    return f"{arc} {circ}"


def catalogue() -> list[PatchEntry]:
    """Return the full patch catalogue. Defined in Task 7 Layer 2."""
    raise NotImplementedError("Layer 2")
