"""Fetch WakaTime coding statistics for the last 7 days via the Summaries API."""

import os
import base64
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Optional

import requests


def fetch_wakatime_stats(api_key: Optional[str] = None) -> dict:
    """
    Fetch coding statistics from the WakaTime Summaries API.

    Uses /summaries instead of /stats to avoid WakaTime's server-side
    caching which can lag hours behind actual activity.

    Args:
        api_key: WakaTime API key. Falls back to WAKATIME_API_KEY env var.

    Returns:
        Dictionary with languages, total_hours, and status.
    """
    api_key = api_key or os.environ.get("WAKATIME_API_KEY")

    if not api_key:
        return _empty_stats("No API key configured")

    try:
        encoded_key = base64.b64encode(api_key.encode()).decode()
        headers = {"Authorization": f"Basic {encoded_key}"}

        today = datetime.now(timezone.utc).date()
        start = today - timedelta(days=6)

        response = requests.get(
            "https://wakatime.com/api/v1/users/current/summaries",
            headers=headers,
            params={"start": str(start), "end": str(today)},
            timeout=30,
        )

        if response.status_code == 401:
            return _empty_stats("Invalid API key")

        if response.status_code == 429:
            return _empty_stats("Rate limited")

        if response.status_code != 200:
            return _empty_stats(f"API error: {response.status_code}")

        payload = response.json()
        days = payload.get("data", [])

        # Aggregate language seconds across all days
        lang_seconds = defaultdict(float)
        total_seconds = 0.0

        for day in days:
            total_seconds += day.get("grand_total", {}).get("total_seconds", 0)
            for lang in day.get("languages", []):
                lang_seconds[lang["name"]] += lang.get("total_seconds", 0)

        # Sort by total time descending, take top 3
        sorted_langs = sorted(lang_seconds.items(), key=lambda x: x[1], reverse=True)
        languages = []
        for name, secs in sorted_langs[:3]:
            pct = (secs / total_seconds * 100) if total_seconds > 0 else 0
            languages.append({
                "name": name,
                "hours": round(secs / 3600, 1),
                "percent": round(pct, 1),
            })

        total_hours = round(total_seconds / 3600, 1)

        return {
            "languages": languages,
            "total_hours": total_hours,
            "status": "ok",
        }

    except requests.RequestException as e:
        return _empty_stats(f"Network error: {str(e)}")
    except (KeyError, ValueError) as e:
        return _empty_stats(f"Parse error: {str(e)}")


def _empty_stats(reason: str) -> dict:
    """Return empty statistics with a reason."""
    return {
        "languages": [],
        "total_hours": 0,
        "last_updated": "",
        "status": "unavailable",
        "reason": reason,
    }


if __name__ == "__main__":
    import json
    stats = fetch_wakatime_stats()
    print(json.dumps(stats, indent=2))
