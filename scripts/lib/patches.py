"""Patch catalogue: maps source fields to SVG markers and element attributes.

The runner walks ``catalogue()`` and applies each entry to the SVG via
``svg_markers.patch_marker`` (for text content bounded by comment markers)
or ``svg_markers.patch_element_attribute`` (for ring dasharrays and bar widths).
"""

import math
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal

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
    value_fn: Callable[[dict[str, Any]], str]


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
    """Return the full patch catalogue.

    Each entry's ``value_fn`` accepts a ``dict[str, Any]`` keyed by source
    name (``"github_stats"``, ``"grade"``, ``"github_contrib"``, ``"wakatime"``,
    ``"uptime"``) and returns the string to write into the SVG.
    """
    entries: list[PatchEntry] = []

    entries.append(
        PatchEntry(
            "github_stats",
            "marker",
            "STARS",
            None,
            lambda r: r["github_stats"].stars_display,
        )
    )
    entries.append(
        PatchEntry(
            "github_stats",
            "marker",
            "COMMITS",
            None,
            lambda r: r["github_stats"].commits_display,
        )
    )
    entries.append(
        PatchEntry(
            "github_stats",
            "marker",
            "PRS",
            None,
            lambda r: r["github_stats"].prs_display,
        )
    )
    entries.append(
        PatchEntry(
            "github_stats",
            "marker",
            "ISSUES",
            None,
            lambda r: r["github_stats"].issues_display,
        )
    )
    entries.append(
        PatchEntry(
            "github_stats",
            "marker",
            "CONTRIB_TO",
            None,
            lambda r: r["github_stats"].contributed_to_display,
        )
    )

    entries.append(
        PatchEntry("grade", "marker", "GRADE_LETTER", None, lambda r: r["grade"].letter)
    )
    entries.append(
        PatchEntry(
            "grade",
            "attribute",
            "grade-ring",
            "stroke-dasharray",
            lambda r: grade_dasharray(percentile=r["grade"].percentile),
        )
    )

    entries.append(
        PatchEntry(
            "github_contrib",
            "marker",
            "TOTAL_CONTRIB",
            None,
            lambda r: r["github_contrib"].total_display,
        )
    )
    entries.append(
        PatchEntry(
            "github_contrib",
            "marker",
            "TOTAL_CONTRIB_RANGE",
            None,
            lambda r: r["github_contrib"].total_range_label,
        )
    )
    entries.append(
        PatchEntry(
            "github_contrib",
            "marker",
            "CURRENT_STREAK",
            None,
            lambda r: str(r["github_contrib"].current_streak_days),
        )
    )
    entries.append(
        PatchEntry(
            "github_contrib",
            "marker",
            "CURRENT_STREAK_RANGE",
            None,
            lambda r: r["github_contrib"].current_streak_range_label,
        )
    )
    entries.append(
        PatchEntry(
            "github_contrib",
            "marker",
            "LONGEST_STREAK",
            None,
            lambda r: str(r["github_contrib"].longest_streak_days),
        )
    )
    entries.append(
        PatchEntry(
            "github_contrib",
            "marker",
            "LONGEST_STREAK_RANGE",
            None,
            lambda r: r["github_contrib"].longest_streak_range_label,
        )
    )
    entries.append(
        PatchEntry(
            "github_contrib",
            "attribute",
            "streak-ring",
            "stroke-dasharray",
            lambda r: streak_dasharray(
                current=r["github_contrib"].current_streak_days,
                longest=r["github_contrib"].longest_streak_days,
            ),
        )
    )

    for i in range(5):
        idx: int = i + 1
        entries.append(
            PatchEntry("wakatime", "marker", f"LANG_{idx}_NAME", None, _lang_name(i))
        )
        entries.append(
            PatchEntry("wakatime", "marker", f"LANG_{idx}_VALUE", None, _lang_value(i))
        )
        entries.append(
            PatchEntry(
                "wakatime", "attribute", f"lang-{idx}-bar", "width", _lang_bar(i)
            )
        )

    entries.append(
        PatchEntry("uptime", "marker", "UPTIME", None, lambda r: r["uptime"].value)
    )

    return entries


def _lang_name(i: int) -> Callable[[dict[str, Any]], str]:
    """Return a lookup that yields the i-th language name or empty string."""

    def fn(r: dict[str, Any]) -> str:
        langs = r["wakatime"].languages
        return str(langs[i].name) if i < len(langs) else ""

    return fn


def _lang_value(i: int) -> Callable[[dict[str, Any]], str]:
    """Return a lookup that yields the i-th language display value."""

    def fn(r: dict[str, Any]) -> str:
        langs = r["wakatime"].languages
        return str(langs[i].text) if i < len(langs) else ""

    return fn


def _lang_bar(i: int) -> Callable[[dict[str, Any]], str]:
    """Return a lookup that yields the i-th language bar width in pixels."""

    def fn(r: dict[str, Any]) -> str:
        langs = r["wakatime"].languages
        top_seconds = langs[0].total_seconds if langs else 0.0
        my_seconds = langs[i].total_seconds if i < len(langs) else 0.0
        return str(bar_scale(top_seconds=top_seconds, my_seconds=my_seconds))

    return fn
