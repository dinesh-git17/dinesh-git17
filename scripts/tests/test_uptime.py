"""Tests for the uptime source."""

from datetime import date

import pytest

from scripts.lib.sources import uptime


def test_fetch_returns_years_and_months_string() -> None:
    result = uptime.fetch(today=date(2026, 4, 26))
    assert result.value == "2 years, 7 months"


def test_fetch_handles_same_month() -> None:
    result = uptime.fetch(today=date(2023, 9, 15))
    assert result.value == "0 years, 0 months"


def test_fetch_handles_year_boundary() -> None:
    result = uptime.fetch(today=date(2024, 1, 1))
    assert result.value == "0 years, 4 months"


def test_fetch_uses_today_by_default() -> None:
    result = uptime.fetch()
    assert "years, " in result.value


def test_fetch_raises_when_today_before_epoch() -> None:
    with pytest.raises(ValueError, match="earlier than epoch"):
        uptime.fetch(today=date(2023, 8, 1))
