"""Fetch WakaTime coding statistics for the last 7 days."""

import os
import base64
from typing import Optional
import requests


def fetch_wakatime_stats(api_key: Optional[str] = None) -> dict:
    """
    Fetch coding statistics from WakaTime API.

    Args:
        api_key: WakaTime API key. Falls back to WAKATIME_API_KEY env var.

    Returns:
        Dictionary with languages, total_hours, and last_updated.
    """
    api_key = api_key or os.environ.get("WAKATIME_API_KEY")

    if not api_key:
        return _empty_stats("No API key configured")

    try:
        encoded_key = base64.b64encode(api_key.encode()).decode()
        headers = {"Authorization": f"Basic {encoded_key}"}

        response = requests.get(
            "https://wakatime.com/api/v1/users/current/stats/last_7_days",
            headers=headers,
            timeout=30,
        )

        if response.status_code == 401:
            return _empty_stats("Invalid API key")

        if response.status_code == 429:
            return _empty_stats("Rate limited")

        if response.status_code != 200:
            return _empty_stats(f"API error: {response.status_code}")

        data = response.json().get("data", {})

        languages = []
        for lang in data.get("languages", [])[:3]:
            languages.append({
                "name": lang.get("name", "Unknown"),
                "hours": round(lang.get("total_seconds", 0) / 3600, 1),
                "percent": round(lang.get("percent", 0), 1),
            })

        total_seconds = data.get("total_seconds", 0)
        total_hours = round(total_seconds / 3600, 1)

        return {
            "languages": languages,
            "total_hours": total_hours,
            "last_updated": data.get("modified_at", ""),
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
