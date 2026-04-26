"""Tests for the GitHub contribution source."""

from datetime import date, datetime, timedelta, timezone
from typing import Any

import pytest

from scripts.lib.sources import github_contrib
from scripts.lib.sources.github_contrib import (
    GithubContribResult,
    StreakStats,
    compute_streaks,
    format_range_label,
    year_windows,
)


def _calendar(*pairs: tuple[date, int]) -> list[tuple[date, int]]:
    return list(pairs)


def test_empty_calendar_returns_zero_streaks() -> None:
    streaks = compute_streaks([], today=date(2026, 4, 26))
    assert streaks.current_days == 0
    assert streaks.longest_days == 0
    assert streaks.current_start is None
    assert streaks.current_end is None
    assert streaks.longest_start is None
    assert streaks.longest_end is None


def test_single_day_today_produces_streak_of_one() -> None:
    today = date(2026, 4, 26)
    streaks = compute_streaks(_calendar((today, 1)), today=today)
    assert streaks.current_days == 1
    assert streaks.longest_days == 1
    assert streaks.current_start == today
    assert streaks.current_end == today


def test_thirty_consecutive_days_ending_today() -> None:
    today = date(2026, 4, 26)
    days = [(date.fromordinal(today.toordinal() - i), 1) for i in range(30)]
    days.reverse()
    streaks = compute_streaks(days, today=today)
    assert streaks.current_days == 30
    assert streaks.longest_days == 30
    assert streaks.current_start == days[0][0]
    assert streaks.current_end == today


def test_today_zero_with_yesterday_streak_uses_yesterday_grace() -> None:
    today = date(2026, 4, 26)
    days = [(date.fromordinal(today.toordinal() - i), 1) for i in range(1, 31)]
    days.append((today, 0))
    days.sort(key=lambda x: x[0])
    streaks = compute_streaks(days, today=today)
    assert streaks.current_days == 30
    assert streaks.current_end == date(2026, 4, 25)


def test_streak_ending_two_days_ago_means_current_zero() -> None:
    today = date(2026, 4, 26)
    days: list[tuple[date, int]] = [(date.fromordinal(today.toordinal() - i), 1) for i in range(2, 32)]
    days.append((date.fromordinal(today.toordinal() - 1), 0))
    days.append((today, 0))
    days.sort(key=lambda x: x[0])
    streaks = compute_streaks(days, today=today)
    assert streaks.current_days == 0
    assert streaks.longest_days == 30


def test_broken_pattern_finds_longest_run() -> None:
    today = date(2026, 4, 26)
    days: list[tuple[date, int]] = []
    for i in range(20, 10, -1):
        days.append((date.fromordinal(today.toordinal() - i), 1))
    days.append((date.fromordinal(today.toordinal() - 10), 0))
    for i in range(9, 4, -1):
        days.append((date.fromordinal(today.toordinal() - i), 1))
    days.append((date.fromordinal(today.toordinal() - 4), 0))
    days.append((date.fromordinal(today.toordinal() - 3), 0))
    days.append((date.fromordinal(today.toordinal() - 2), 0))
    days.append((date.fromordinal(today.toordinal() - 1), 0))
    days.append((today, 1))
    streaks = compute_streaks(days, today=today)
    assert streaks.current_days == 1
    assert streaks.longest_days == 10


def test_format_range_label_full_range() -> None:
    assert format_range_label(date(2026, 1, 31), date(2026, 4, 25)) == "Jan 31 - Apr 25"


def test_format_range_label_single_day() -> None:
    assert format_range_label(date(2026, 4, 25), date(2026, 4, 25)) == "Apr 25"
