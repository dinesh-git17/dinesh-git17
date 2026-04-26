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


def test_year_windows_single_window_when_account_under_one_year() -> None:
    epoch = date(2025, 10, 1)
    today = date(2026, 4, 26)
    windows = year_windows(epoch, today)
    assert len(windows) == 1
    assert windows[0][0].year == 2025
    assert windows[0][1].year == 2026


def test_year_windows_tile_multi_year_account_without_overlap() -> None:
    epoch = date(2023, 9, 1)
    today = date(2026, 4, 26)
    windows = year_windows(epoch, today)
    assert len(windows) >= 3
    for i in range(len(windows) - 1):
        assert windows[i][1] <= windows[i + 1][0] + timedelta(microseconds=1) or windows[i][1] == windows[i + 1][0]


def test_year_windows_last_window_ends_at_today() -> None:
    epoch = date(2023, 9, 1)
    today = date(2026, 4, 26)
    windows = year_windows(epoch, today)
    assert windows[-1][1].date() == today


def test_fetch_returns_total_and_streaks(monkeypatch: pytest.MonkeyPatch) -> None:
    today = date(2026, 4, 26)

    def fake_post_json(url: str, headers: dict[str, str], body: dict[str, Any]) -> dict[str, Any]:
        query: str = body["query"]
        variables: dict[str, Any] = body["variables"]
        if "totalContributions" in query:
            return {
                "data": {
                    "user": {
                        "contributionsCollection": {
                            "contributionCalendar": {"totalContributions": 5_981}
                        }
                    }
                }
            }
        return {
            "data": {
                "user": {
                    "contributionsCollection": {
                        "contributionCalendar": {
                            "weeks": [
                                {
                                    "contributionDays": [
                                        {"date": (today - timedelta(days=2)).isoformat(), "contributionCount": 5},
                                        {"date": (today - timedelta(days=1)).isoformat(), "contributionCount": 3},
                                        {"date": today.isoformat(), "contributionCount": 7},
                                    ]
                                }
                            ]
                        }
                    }
                }
            }
        }

    monkeypatch.setattr(github_contrib, "post_json", fake_post_json)
    monkeypatch.setattr(github_contrib, "_today_utc", lambda: today)

    result = github_contrib.fetch(login="dinesh-git17", token="ghp_test")

    assert isinstance(result, GithubContribResult)
    assert result.total_count == 5_981
    assert result.total_display == "5,981"
    assert result.total_range_label == "Jan 1, 2026 - Present"
    assert result.current_streak_days == 3
    assert result.longest_streak_days == 3
    assert result.current_streak_range_label == f"{(today - timedelta(days=2)).strftime('%b')} {(today - timedelta(days=2)).day} - {today.strftime('%b')} {today.day}"


def test_fetch_concatenates_multiple_year_windows(monkeypatch: pytest.MonkeyPatch) -> None:
    today = date(2026, 4, 26)
    calendar_calls: list[tuple[str, str]] = []

    def fake_post_json(url: str, headers: dict[str, str], body: dict[str, Any]) -> dict[str, Any]:
        query: str = body["query"]
        if "totalContributions" in query:
            return {
                "data": {
                    "user": {
                        "contributionsCollection": {
                            "contributionCalendar": {"totalContributions": 100}
                        }
                    }
                }
            }
        variables: dict[str, Any] = body["variables"]
        calendar_calls.append((variables["from"], variables["to"]))
        return {
            "data": {
                "user": {
                    "contributionsCollection": {
                        "contributionCalendar": {"weeks": []}
                    }
                }
            }
        }

    monkeypatch.setattr(github_contrib, "post_json", fake_post_json)
    monkeypatch.setattr(github_contrib, "_today_utc", lambda: today)

    github_contrib.fetch(login="dinesh-git17", token="ghp_test")

    assert len(calendar_calls) >= 3
