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
