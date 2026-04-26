"""GitHub contribution source: calendar-year total + all-time streaks."""

import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

_GRAPHQL_ENDPOINT: str = "https://api.github.com/graphql"
_ACCOUNT_EPOCH: date = date(2023, 9, 1)
_TOTAL_QUERY: str = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar { totalContributions }
    }
  }
}
"""
_CALENDAR_QUERY: str = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        weeks {
          contributionDays { date contributionCount }
        }
      }
    }
  }
}
"""


@dataclass(frozen=True)
class StreakStats:
    """Current and longest streak with start/end dates."""

    current_days: int
    current_start: date | None
    current_end: date | None
    longest_days: int
    longest_start: date | None
    longest_end: date | None


@dataclass(frozen=True)
class GithubContribResult:
    """Result of a GitHub contribution fetch."""

    total_count: int
    total_display: str
    total_range_label: str
    current_streak_days: int
    current_streak_range_label: str
    longest_streak_days: int
    longest_streak_range_label: str


def compute_streaks(calendar: list[tuple[date, int]], *, today: date) -> StreakStats:
    """Walk a chronological list of ``(date, contribution_count)`` and return the streaks.

    The walker applies today-zero grace: when today has zero contributions but
    yesterday is non-zero, the current streak still ends at yesterday rather
    than breaking.
    """
    if not calendar:
        return StreakStats(
            current_days=0,
            current_start=None,
            current_end=None,
            longest_days=0,
            longest_start=None,
            longest_end=None,
        )

    longest_days: int = 0
    longest_start: date | None = None
    longest_end: date | None = None
    run_days: int = 0
    run_start: date | None = None
    for day, count in calendar:
        if count > 0:
            if run_days == 0:
                run_start = day
            run_days += 1
            if run_days > longest_days:
                longest_days = run_days
                longest_start = run_start
                longest_end = day
        else:
            run_days = 0
            run_start = None

    current_days: int = 0
    current_start: date | None = None
    current_end: date | None = None
    by_date: dict[date, int] = dict(calendar)
    cursor: date = today
    if by_date.get(today, 0) == 0 and by_date.get(today - timedelta(days=1), 0) > 0:
        cursor = today - timedelta(days=1)
    while by_date.get(cursor, 0) > 0:
        if current_end is None:
            current_end = cursor
        current_start = cursor
        current_days += 1
        cursor -= timedelta(days=1)
    return StreakStats(
        current_days=current_days,
        current_start=current_start,
        current_end=current_end,
        longest_days=longest_days,
        longest_start=longest_start,
        longest_end=longest_end,
    )


def format_range_label(start: date, end: date) -> str:
    """Return a label like ``"Jan 31 - Apr 25"``. Single-day returns ``"Apr 25"``."""
    if start == end:
        return f"{end.strftime('%b')} {end.day}"
    return f"{start.strftime('%b')} {start.day} - {end.strftime('%b')} {end.day}"


def year_windows(account_epoch: date, today: date) -> list[tuple[datetime, datetime]]:
    """Return year-long ``(from, to)`` windows that tile ``[account_epoch, today]``.

    Each window is at most 365 days; the last window ends at ``today``. Returned
    datetimes are UTC-aware and the windows do not overlap.
    """
    windows: list[tuple[datetime, datetime]] = []
    cursor: datetime = datetime.combine(account_epoch, datetime.min.time(), tzinfo=timezone.utc)
    end: datetime = datetime.combine(today, datetime.max.time().replace(microsecond=0), tzinfo=timezone.utc)
    while cursor < end:
        next_cursor: datetime = cursor + timedelta(days=365)
        windows.append((cursor, min(next_cursor, end)))
        cursor = next_cursor
    return windows


def _post_json(url: str, headers: dict[str, str], body: dict[str, Any]) -> dict[str, Any]:
    """POST JSON to ``url``; return the parsed response."""
    payload: bytes = json.dumps(body).encode("utf-8")
    request = Request(url, data=payload, headers=headers, method="POST")
    try:
        with urlopen(request, timeout=30) as response:
            text: str = response.read().decode("utf-8")
    except HTTPError:
        raise
    except URLError as exc:
        msg = f"network error for {url}: {exc.reason}"
        raise ConnectionError(msg) from exc
    return json.loads(text)


def _today_utc() -> date:
    """Return today's date in UTC. Override target in tests."""
    return datetime.now(timezone.utc).date()


def fetch(*, login: str, token: str) -> GithubContribResult:
    """Fetch the calendar-year total and all-time streaks for ``login``.

    Args:
        login: The GitHub user login (e.g., ``"dinesh-git17"``).
        token: A personal access token with ``read:user`` scope.

    Returns:
        ``GithubContribResult`` populated with total + streak fields.
    """
    headers: dict[str, str] = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "dinesh-git17-dashboard",
    }
    today: date = _today_utc()
    year_start: datetime = datetime(today.year, 1, 1, tzinfo=timezone.utc)
    now: datetime = datetime.combine(today, datetime.max.time().replace(microsecond=0), tzinfo=timezone.utc)

    total_response: dict[str, Any] = _post_json(
        _GRAPHQL_ENDPOINT,
        headers,
        {
            "query": _TOTAL_QUERY,
            "variables": {
                "login": login,
                "from": year_start.isoformat().replace("+00:00", "Z"),
                "to": now.isoformat().replace("+00:00", "Z"),
            },
        },
    )
    total_count: int = total_response["data"]["user"]["contributionsCollection"]["contributionCalendar"]["totalContributions"]

    by_date: dict[date, int] = {}
    for window_from, window_to in year_windows(_ACCOUNT_EPOCH, today):
        response: dict[str, Any] = _post_json(
            _GRAPHQL_ENDPOINT,
            headers,
            {
                "query": _CALENDAR_QUERY,
                "variables": {
                    "login": login,
                    "from": window_from.isoformat().replace("+00:00", "Z"),
                    "to": window_to.isoformat().replace("+00:00", "Z"),
                },
            },
        )
        weeks: list[dict[str, Any]] = response["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
        for week in weeks:
            for day in week["contributionDays"]:
                day_date: date = date.fromisoformat(day["date"])
                by_date[day_date] = day["contributionCount"]
    calendar: list[tuple[date, int]] = sorted(by_date.items())

    streaks: StreakStats = compute_streaks(calendar, today=today)

    current_label: str = (
        format_range_label(streaks.current_start, streaks.current_end)
        if streaks.current_start is not None and streaks.current_end is not None
        else ""
    )
    longest_label: str = (
        format_range_label(streaks.longest_start, streaks.longest_end)
        if streaks.longest_start is not None and streaks.longest_end is not None
        else ""
    )

    return GithubContribResult(
        total_count=total_count,
        total_display=f"{total_count:,}",
        total_range_label=f"Jan 1, {today.year} - Present",
        current_streak_days=streaks.current_days,
        current_streak_range_label=current_label,
        longest_streak_days=streaks.longest_days,
        longest_streak_range_label=longest_label,
    )
