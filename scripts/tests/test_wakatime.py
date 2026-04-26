"""Tests for the WakaTime source."""

from typing import Any

import pytest

from scripts.lib import http
from scripts.lib.sources import wakatime
from scripts.lib.sources.wakatime import LanguageEntry, WakatimeResult


def _canned_response() -> dict[str, Any]:
    return {
        "data": {
            "languages": [
                {"name": "Python", "text": "30 hrs", "total_seconds": 108_000.0},
                {"name": "Other", "text": "9 hrs 35 mins", "total_seconds": 34_500.0},
                {
                    "name": "TypeScript",
                    "text": "5 hrs 12 mins",
                    "total_seconds": 18_720.0,
                },
                {
                    "name": "JavaScript",
                    "text": "3 hrs 9 mins",
                    "total_seconds": 11_340.0,
                },
                {"name": "YAML", "text": "1 hr 25 mins", "total_seconds": 5_100.0},
                {"name": "Bash", "text": "1 hr 24 mins", "total_seconds": 5_040.0},
                {"name": "Rust", "text": "45 mins", "total_seconds": 2_700.0},
                {"name": "Markdown", "text": "30 mins", "total_seconds": 1_800.0},
            ]
        }
    }


def test_fetch_returns_top_five_languages(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        http, "get_json", lambda url, headers, timeout=30: _canned_response()
    )

    result = wakatime.fetch(username="dinbuilds")

    assert isinstance(result, WakatimeResult)
    assert len(result.languages) == 5
    assert all(isinstance(entry, LanguageEntry) for entry in result.languages)
    assert result.languages[0].name == "Python"
    assert result.languages[0].text == "30 hrs"
    assert result.languages[0].total_seconds == 108_000.0
    assert result.languages[4].name == "Rust"


def test_fetch_excludes_markup_and_bucket_languages(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        http, "get_json", lambda url, headers, timeout=30: _canned_response()
    )

    result = wakatime.fetch(username="dinbuilds")

    names = {entry.name for entry in result.languages}
    assert names.isdisjoint({"Markdown", "YAML", "Other"})
    assert names == {"Python", "TypeScript", "JavaScript", "Bash", "Rust"}


def test_fetch_preserves_api_sort_order(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        http, "get_json", lambda url, headers, timeout=30: _canned_response()
    )

    result = wakatime.fetch(username="dinbuilds")

    seconds = [entry.total_seconds for entry in result.languages]
    assert seconds == sorted(seconds, reverse=True)


def test_fetch_handles_fewer_than_five_languages(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response = {
        "data": {
            "languages": [
                {"name": "Python", "text": "5 hrs", "total_seconds": 18_000.0},
                {"name": "Bash", "text": "1 hr", "total_seconds": 3_600.0},
            ]
        }
    }
    monkeypatch.setattr(http, "get_json", lambda url, headers, timeout=30: response)

    result = wakatime.fetch(username="dinbuilds")
    assert len(result.languages) == 2


def test_fetch_sends_no_auth_when_api_key_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    def fake_get_json(
        url: str, headers: dict[str, str], timeout: int = 30
    ) -> dict[str, Any]:
        captured["url"] = url
        captured["headers"] = headers
        return _canned_response()

    monkeypatch.setattr(http, "get_json", fake_get_json)

    wakatime.fetch(username="dinbuilds", api_key=None)

    assert "Authorization" not in captured["headers"]
    assert (
        captured["url"]
        == "https://wakatime.com/api/v1/users/dinbuilds/stats/last_7_days"
    )


def test_fetch_sends_basic_auth_when_api_key_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    def fake_get_json(
        url: str, headers: dict[str, str], timeout: int = 30
    ) -> dict[str, Any]:
        captured["headers"] = headers
        return _canned_response()

    monkeypatch.setattr(http, "get_json", fake_get_json)

    wakatime.fetch(username="dinbuilds", api_key="waka_secret")

    assert captured["headers"]["Authorization"].startswith("Basic ")
