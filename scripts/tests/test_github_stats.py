"""Tests for the GitHub stats source."""

from typing import Any

import pytest

from scripts.lib.sources import github_stats
from scripts.lib.sources.github_stats import GithubStatsResult, abbreviate


def test_abbreviate_under_thousand_returns_integer_string() -> None:
    assert abbreviate(0) == "0"
    assert abbreviate(36) == "36"
    assert abbreviate(818) == "818"
    assert abbreviate(999) == "999"


def test_abbreviate_thousands_uses_k_suffix() -> None:
    assert abbreviate(1000) == "1k"
    assert abbreviate(1200) == "1.2k"
    assert abbreviate(3800) == "3.8k"
    assert abbreviate(10_000) == "10k"
    assert abbreviate(999_499) == "999.5k"


def test_abbreviate_millions_uses_m_suffix() -> None:
    assert abbreviate(1_000_000) == "1M"
    assert abbreviate(1_500_000) == "1.5M"


def _canned_graphql_response(
    *,
    followers: int = 20,
    repo_stars: list[int] | None = None,
    commits: int = 3800,
    prs: int = 818,
    issues: int = 36,
    reviews: int = 10,
    contributed_to: int = 3,
) -> dict[str, Any]:
    if repo_stars is None:
        repo_stars = [50, 30, 20, 10, 6]
    return {
        "data": {
            "user": {
                "followers": {"totalCount": followers},
                "repositories": {
                    "totalCount": len(repo_stars),
                    "nodes": [{"stargazerCount": n} for n in repo_stars],
                },
                "contributionsCollection": {
                    "totalCommitContributions": commits,
                    "totalPullRequestContributions": prs,
                    "totalIssueContributions": issues,
                    "totalPullRequestReviewContributions": reviews,
                    "totalRepositoriesWithContributedCommits": contributed_to,
                },
            }
        }
    }


def test_fetch_extracts_all_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def fake_post_json(url: str, headers: dict[str, str], body: dict[str, Any]) -> dict[str, Any]:
        captured["url"] = url
        captured["headers"] = headers
        captured["body"] = body
        return _canned_graphql_response()

    monkeypatch.setattr(github_stats, "_post_json", fake_post_json)

    result = github_stats.fetch(login="dinesh-git17", token="ghp_test")

    assert isinstance(result, GithubStatsResult)
    assert result.stars == 116
    assert result.commits == 3800
    assert result.prs == 818
    assert result.issues == 36
    assert result.reviews == 10
    assert result.contributed_to == 3
    assert result.followers == 20
    assert result.stars_display == "116"
    assert result.commits_display == "3.8k"
    assert result.prs_display == "818"
    assert result.issues_display == "36"
    assert result.contributed_to_display == "3"


def test_fetch_sends_bearer_token_header(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def fake_post_json(url: str, headers: dict[str, str], body: dict[str, Any]) -> dict[str, Any]:
        captured["headers"] = headers
        return _canned_graphql_response()

    monkeypatch.setattr(github_stats, "_post_json", fake_post_json)
    github_stats.fetch(login="dinesh-git17", token="ghp_test")

    assert captured["headers"]["Authorization"] == "Bearer ghp_test"
    assert captured["headers"]["Content-Type"] == "application/json"


def test_fetch_raises_when_repo_count_exceeds_window(monkeypatch: pytest.MonkeyPatch) -> None:
    response = _canned_graphql_response(repo_stars=[1] * 50)
    response["data"]["user"]["repositories"]["totalCount"] = 150

    monkeypatch.setattr(github_stats, "_post_json", lambda *a, **k: response)

    with pytest.raises(ValueError, match="exceeds 100"):
        github_stats.fetch(login="dinesh-git17", token="ghp_test")


def test_fetch_handles_zero_stars(monkeypatch: pytest.MonkeyPatch) -> None:
    response = _canned_graphql_response(repo_stars=[0, 0, 0])
    monkeypatch.setattr(github_stats, "_post_json", lambda *a, **k: response)

    result = github_stats.fetch(login="dinesh-git17", token="ghp_test")
    assert result.stars == 0
    assert result.stars_display == "0"


def test_fetch_handles_no_repositories(monkeypatch: pytest.MonkeyPatch) -> None:
    response = _canned_graphql_response(repo_stars=[])
    monkeypatch.setattr(github_stats, "_post_json", lambda *a, **k: response)

    result = github_stats.fetch(login="dinesh-git17", token="ghp_test")
    assert result.stars == 0
