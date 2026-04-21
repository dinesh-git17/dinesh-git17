"""Rewrite the cache-buster ``v`` query param on the stats card URLs in README.md.

Runs idempotently per-day on schedule (rolls the date over), and bumps the
monotonic suffix on manual dispatches to flush the Vercel and camo caches.
"""

import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

REPO_ROOT: Path = Path(__file__).resolve().parent.parent
README_PATH: Path = REPO_ROOT / "README.md"
EXPECTED_URL_COUNT: int = 3

URL_PATTERN: re.Pattern[str] = re.compile(
    r"https://github-readme-(?:stats-inky-three-53|streak-stats-ivory-eta-73)"
    r"\.vercel\.app[^\s\"'<>]+"
)
V_PATTERN: re.Pattern[str] = re.compile(
    r"^(?P<date>\d{4}-\d{2}-\d{2})\.(?P<n>\d+)$"
)


def compute_next_v(current_v: str | None, today: date) -> str:
    """Return the next cache-buster value.

    The new suffix is ``(current suffix for today) + 1``, or ``1`` if the
    date rolled over or ``current_v`` is ``None``.

    Args:
        current_v: The current ``v`` parameter value, or ``None`` if absent.
            Expected shape is ``YYYY-MM-DD.N`` where N is a positive integer.
        today: The reference date (usually ``date.today()``).

    Returns:
        A string of shape ``YYYY-MM-DD.N``.

    Raises:
        ValueError: If ``current_v`` is non-None and does not match the
            expected pattern.
    """
    today_str: str = today.isoformat()
    if current_v is None:
        return f"{today_str}.1"
    match: re.Match[str] | None = V_PATTERN.match(current_v)
    if match is None:
        msg = f"malformed v value: {current_v!r}"
        raise ValueError(msg)
    existing_date: str = match.group("date")
    existing_n: int = int(match.group("n"))
    if existing_date == today_str:
        return f"{today_str}.{existing_n + 1}"
    return f"{today_str}.1"


def _extract_v(url: str) -> str | None:
    """Return the ``v`` query parameter from ``url``, or ``None`` if absent."""
    query: str = urlsplit(url).query
    for key, value in parse_qsl(query, keep_blank_values=True):
        if key == "v":
            return value
    return None


def update_v_param(url: str, new_v: str) -> str:
    """Return ``url`` with its ``v`` query parameter replaced by ``new_v``.

    All other query parameters are preserved in their original order; any
    pre-existing ``v`` is dropped. ``new_v`` is appended at the end.

    Args:
        url: An absolute URL with a query string.
        new_v: The replacement value (e.g. ``"2026-04-21.1"``).

    Returns:
        The reassembled URL string.
    """
    parts = urlsplit(url)
    kept: list[tuple[str, str]] = [
        (k, v)
        for k, v in parse_qsl(parts.query, keep_blank_values=True)
        if k != "v"
    ]
    kept.append(("v", new_v))
    new_query: str = urlencode(kept)
    return urlunsplit(
        (parts.scheme, parts.netloc, parts.path, new_query, parts.fragment)
    )


def main() -> int:
    """Entry point. Returns process exit code."""
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
