"""WakaTime source: top 5 languages by hours, last 7 days.

Markup and bucket categories (Markdown, YAML, "Other") are filtered out before
the top-N slice so the dashboard only surfaces actual programming languages.
"""

import base64
from dataclasses import dataclass
from typing import Any

from scripts.lib import http

_ENDPOINT_TEMPLATE: str = (
    "https://wakatime.com/api/v1/users/{username}/stats/last_7_days"
)
_TOP_N: int = 5
_EXCLUDED_LANGUAGES: frozenset[str] = frozenset({"Markdown", "YAML", "Other"})


@dataclass(frozen=True)
class LanguageEntry:
    """One language row from WakaTime stats."""

    name: str
    text: str
    total_seconds: float


@dataclass(frozen=True)
class WakatimeResult:
    """Result of a WakaTime fetch."""

    languages: list[LanguageEntry]


def fetch(*, username: str, api_key: str | None = None) -> WakatimeResult:
    """Fetch top-5 languages for ``username`` over the last 7 days.

    Args:
        username: The public WakaTime username (e.g., ``"dinbuilds"``).
        api_key: Optional API key. When set, sends Basic auth so the call
            still works if the account is private.

    Returns:
        ``WakatimeResult`` with up to 5 ``LanguageEntry`` rows in API order.
    """
    headers: dict[str, str] = {"User-Agent": "dinesh-git17-dashboard"}
    if api_key is not None:
        encoded: str = base64.b64encode(api_key.encode("utf-8")).decode("ascii")
        headers["Authorization"] = f"Basic {encoded}"
    url: str = _ENDPOINT_TEMPLATE.format(username=username)
    body: dict[str, Any] = http.get_json(url, headers=headers)
    raw_languages: list[dict[str, Any]] = body["data"]["languages"]
    filtered: list[dict[str, Any]] = [
        row for row in raw_languages if row["name"] not in _EXCLUDED_LANGUAGES
    ]
    entries: list[LanguageEntry] = [
        LanguageEntry(
            name=row["name"],
            text=row["text"],
            total_seconds=float(row["total_seconds"]),
        )
        for row in filtered[:_TOP_N]
    ]
    return WakatimeResult(languages=entries)
