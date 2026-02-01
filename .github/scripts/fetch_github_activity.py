"""Fetch GitHub contribution activity via GraphQL API."""

import os
from datetime import datetime, timedelta
from typing import Optional
import requests


GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"


def fetch_contribution_data(
    username: str = "dinesh-git17",
    token: Optional[str] = None,
) -> dict:
    """
    Fetch contribution calendar data from GitHub GraphQL API.

    Args:
        username: GitHub username.
        token: GitHub token. Falls back to GITHUB_TOKEN env var.

    Returns:
        Dictionary with weeks of contribution data.
    """
    token = token or os.environ.get("GITHUB_TOKEN")

    if not token:
        return _empty_data("No GitHub token configured")

    query = """
    query($username: String!) {
      user(login: $username) {
        contributionsCollection {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                contributionCount
                date
                weekday
              }
            }
          }
        }
      }
    }
    """

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            GITHUB_GRAPHQL_URL,
            json={"query": query, "variables": {"username": username}},
            headers=headers,
            timeout=30,
        )

        if response.status_code != 200:
            return _empty_data(f"API error: {response.status_code}")

        data = response.json()

        if "errors" in data:
            return _empty_data(f"GraphQL error: {data['errors'][0]['message']}")

        calendar = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]

        # Get last 12 weeks of data for the circuit visualization
        weeks = calendar["weeks"][-12:]

        # Transform into circuit-friendly format
        nodes = []
        max_count = 1

        for week_idx, week in enumerate(weeks):
            for day in week["contributionDays"]:
                count = day["contributionCount"]
                max_count = max(max_count, count)
                nodes.append({
                    "week": week_idx,
                    "weekday": day["weekday"],
                    "count": count,
                    "date": day["date"],
                })

        # Calculate intensity levels (0-4)
        for node in nodes:
            if node["count"] == 0:
                node["level"] = 0
            else:
                ratio = node["count"] / max_count
                if ratio < 0.25:
                    node["level"] = 1
                elif ratio < 0.5:
                    node["level"] = 2
                elif ratio < 0.75:
                    node["level"] = 3
                else:
                    node["level"] = 4

        return {
            "total": calendar["totalContributions"],
            "nodes": nodes,
            "weeks_count": len(weeks),
            "max_count": max_count,
            "status": "ok",
        }

    except requests.RequestException as e:
        return _empty_data(f"Network error: {str(e)}")
    except (KeyError, ValueError, TypeError) as e:
        return _empty_data(f"Parse error: {str(e)}")


def _empty_data(reason: str) -> dict:
    """Return empty data with reason."""
    return {
        "total": 0,
        "nodes": [],
        "weeks_count": 0,
        "max_count": 0,
        "status": "unavailable",
        "reason": reason,
    }


if __name__ == "__main__":
    import json
    data = fetch_contribution_data()
    print(json.dumps(data, indent=2))
