"""Tests for the patch catalogue and helpers."""

from pathlib import Path

import pytest

from scripts.lib import patches
from scripts.lib.patches import (
    GRADE_RING_RADIUS,
    STREAK_RING_RADIUS,
    LANG_BAR_CAP,
    LANG_BAR_TRACK,
    PatchEntry,
    bar_scale,
    catalogue,
    grade_dasharray,
    ring_circumference,
    streak_dasharray,
)


def test_bar_scale_top_row_lands_at_cap() -> None:
    assert bar_scale(top_seconds=1000.0, my_seconds=1000.0) == LANG_BAR_CAP


def test_bar_scale_proportional_below_top() -> None:
    assert bar_scale(top_seconds=1000.0, my_seconds=500.0) == round(LANG_BAR_CAP * 0.5)


def test_bar_scale_floor_for_tiny_values() -> None:
    assert bar_scale(top_seconds=10_000.0, my_seconds=1.0) == 2


def test_bar_scale_zero_top_returns_floor() -> None:
    assert bar_scale(top_seconds=0.0, my_seconds=0.0) == 2


def test_ring_circumference_uses_drawn_radius() -> None:
    assert ring_circumference(GRADE_RING_RADIUS) == round(2 * 3.141592653589793 * GRADE_RING_RADIUS)
    assert ring_circumference(STREAK_RING_RADIUS) == round(2 * 3.141592653589793 * STREAK_RING_RADIUS)


def test_grade_dasharray_low_percentile_long_arc() -> None:
    arc = grade_dasharray(percentile=25.0)
    circ = ring_circumference(GRADE_RING_RADIUS)
    assert arc == f"{round(circ * 0.75)} {circ}"


def test_grade_dasharray_high_percentile_short_arc() -> None:
    arc = grade_dasharray(percentile=87.5)
    circ = ring_circumference(GRADE_RING_RADIUS)
    assert arc == f"{round(circ * 0.125)} {circ}"


def test_streak_dasharray_at_record_is_full() -> None:
    arc = streak_dasharray(current=85, longest=85)
    circ = ring_circumference(STREAK_RING_RADIUS)
    assert arc == f"{circ} {circ}"


def test_streak_dasharray_below_record_is_proportional() -> None:
    arc = streak_dasharray(current=42, longest=85)
    circ = ring_circumference(STREAK_RING_RADIUS)
    assert arc == f"{round(circ * 42 / 85)} {circ}"


def test_streak_dasharray_zero_longest_returns_zero_arc() -> None:
    arc = streak_dasharray(current=0, longest=0)
    circ = ring_circumference(STREAK_RING_RADIUS)
    assert arc == f"0 {circ}"


def test_streak_dasharray_clamps_to_full() -> None:
    arc = streak_dasharray(current=100, longest=85)
    circ = ring_circumference(STREAK_RING_RADIUS)
    assert arc == f"{circ} {circ}"


def test_catalogue_entries_resolve_against_real_svg(repo_root: Path) -> None:
    svg_path: Path = repo_root / "assets" / "dashboard.svg"
    content: str = svg_path.read_text(encoding="utf-8")
    entries = catalogue()
    assert len(entries) > 0
    for entry in entries:
        if entry.target_kind == "marker":
            assert f"<!-- {entry.target_id}_START -->" in content, (
                f"marker {entry.target_id} missing from SVG"
            )
            assert f"<!-- {entry.target_id}_END -->" in content
        elif entry.target_kind == "attribute":
            assert f'id="{entry.target_id}"' in content, (
                f"element id {entry.target_id} missing from SVG"
            )
            assert entry.attribute_name is not None


def test_catalogue_covers_all_documented_targets() -> None:
    entries = catalogue()
    marker_ids = {e.target_id for e in entries if e.target_kind == "marker"}
    expected_markers: set[str] = {
        "STARS", "COMMITS", "PRS", "ISSUES", "CONTRIB_TO",
        "GRADE_LETTER",
        "TOTAL_CONTRIB", "TOTAL_CONTRIB_RANGE",
        "CURRENT_STREAK", "CURRENT_STREAK_RANGE",
        "LONGEST_STREAK", "LONGEST_STREAK_RANGE",
        "LANG_1_NAME", "LANG_2_NAME", "LANG_3_NAME", "LANG_4_NAME", "LANG_5_NAME",
        "LANG_1_VALUE", "LANG_2_VALUE", "LANG_3_VALUE", "LANG_4_VALUE", "LANG_5_VALUE",
        "UPTIME",
    }
    assert expected_markers.issubset(marker_ids)
    attr_ids = {e.target_id for e in entries if e.target_kind == "attribute"}
    assert {"grade-ring", "streak-ring", "lang-1-bar", "lang-2-bar", "lang-3-bar", "lang-4-bar", "lang-5-bar"}.issubset(attr_ids)


def test_value_fns_handle_real_shaped_inputs() -> None:
    entries = catalogue()
    fake_results: dict = {
        "github_stats": type("GS", (), {
            "stars_display": "116", "commits_display": "3.8k",
            "prs_display": "818", "issues_display": "36",
            "contributed_to_display": "3",
        })(),
        "grade": type("GR", (), {"letter": "A", "percentile": 25.0})(),
        "github_contrib": type("GC", (), {
            "total_count": 5_981, "total_display": "5,981",
            "total_range_label": "Jan 1, 2026 - Present",
            "current_streak_days": 85, "current_streak_range_label": "Jan 31 - Apr 25",
            "longest_streak_days": 85, "longest_streak_range_label": "Jan 31 - Apr 25",
        })(),
        "wakatime": type("WT", (), {
            "languages": [
                type("L", (), {"name": "Python", "text": "30 hrs", "total_seconds": 108_000.0})(),
                type("L", (), {"name": "Other", "text": "9 hrs 35 mins", "total_seconds": 34_500.0})(),
                type("L", (), {"name": "JavaScript", "text": "3 hrs 9 mins", "total_seconds": 11_340.0})(),
                type("L", (), {"name": "YAML", "text": "1 hr 25 mins", "total_seconds": 5_100.0})(),
                type("L", (), {"name": "Bash", "text": "1 hr 24 mins", "total_seconds": 5_040.0})(),
            ],
        })(),
        "uptime": type("UT", (), {"value": "2 years, 7 months"})(),
    }
    for entry in entries:
        out: str = entry.value_fn(fake_results)
        assert isinstance(out, str)
        assert len(out) > 0
