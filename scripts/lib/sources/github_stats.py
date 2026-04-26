"""GitHub stats source: stars, commits, PRs, issues, reviews, contributed-to."""

from dataclasses import dataclass
from typing import Any

from scripts.lib.http import post_json

_GRAPHQL_ENDPOINT: str = "https://api.github.com/graphql"
_REPO_WINDOW: int = 100
_MILLION: int = 1_000_000
_THOUSAND: int = 1_000

_QUERY: str = """
query($login: String!) {
  user(login: $login) {
    followers { totalCount }
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false) {
      totalCount
      nodes { stargazerCount }
    }
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      totalPullRequestReviewContributions
      totalRepositoriesWithContributedCommits
    }
  }
}
"""


@dataclass(frozen=True)
class GithubStatsResult:
    """Result of a GitHub stats fetch."""

    stars: int
    commits: int
    prs: int
    issues: int
    reviews: int
    contributed_to: int
    followers: int
    stars_display: str
    commits_display: str
    prs_display: str
    issues_display: str
    contributed_to_display: str


def abbreviate(n: int) -> str:
    """Format a count as ``"3.8k"``, ``"1.5M"``, or the plain integer string.

    Trims trailing ``".0"``. Uses one decimal of precision for thousands and millions.
    """
    if n >= _MILLION:
        formatted: str = f"{n / _MILLION:.1f}M"
    elif n >= _THOUSAND:
        formatted = f"{n / _THOUSAND:.1f}k"
    else:
        return str(n)
    return formatted.replace(".0", "", 1)


def fetch(*, login: str, token: str) -> GithubStatsResult:
    """Fetch GitHub stats for ``login`` using the bearer ``token``.

    Args:
        login: The GitHub user login (e.g., ``"dinesh-git17"``).
        token: A personal access token with ``read:user`` and ``repo`` scopes.

    Returns:
        ``GithubStatsResult`` populated with raw counts and display strings.

    Raises:
        ValueError: If the user owns more than ``_REPO_WINDOW`` non-fork repos
            (the query is not paginated).
        HTTPError: If the GraphQL endpoint returns a non-2xx status.
        ConnectionError: If the transport fails.
    """
    headers: dict[str, str] = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "dinesh-git17-dashboard",
    }
    body: dict[str, Any] = {"query": _QUERY, "variables": {"login": login}}
    response: dict[str, Any] = post_json(_GRAPHQL_ENDPOINT, headers, body)
    user: dict[str, Any] = response["data"]["user"]

    repos: dict[str, Any] = user["repositories"]
    if repos["totalCount"] > _REPO_WINDOW:
        msg = (
            f"owned repo count ({repos['totalCount']}) "
            f"exceeds {_REPO_WINDOW}; pagination required"
        )
        raise ValueError(msg)
    stars: int = sum(node["stargazerCount"] for node in repos["nodes"])

    contrib: dict[str, Any] = user["contributionsCollection"]
    commits: int = contrib["totalCommitContributions"]
    prs: int = contrib["totalPullRequestContributions"]
    issues: int = contrib["totalIssueContributions"]
    reviews: int = contrib["totalPullRequestReviewContributions"]
    contributed_to: int = contrib["totalRepositoriesWithContributedCommits"]
    followers: int = user["followers"]["totalCount"]

    return GithubStatsResult(
        stars=stars,
        commits=commits,
        prs=prs,
        issues=issues,
        reviews=reviews,
        contributed_to=contributed_to,
        followers=followers,
        stars_display=abbreviate(stars),
        commits_display=abbreviate(commits),
        prs_display=abbreviate(prs),
        issues_display=abbreviate(issues),
        contributed_to_display=abbreviate(contributed_to),
    )
