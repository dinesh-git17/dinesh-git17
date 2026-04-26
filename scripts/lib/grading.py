"""Grade calculation, ported from github-readme-stats calculateRank.js.

Pure function: same inputs always produce the same output. The medians,
weights, thresholds, and CDF approximations are copied verbatim from the
reference implementation at
``https://github.com/anuraghazra/github-readme-stats/blob/master/src/calculateRank.js``.
"""

from dataclasses import dataclass

_COMMITS_MEDIAN: int = 1000
_PRS_MEDIAN: int = 50
_ISSUES_MEDIAN: int = 25
_REVIEWS_MEDIAN: int = 2
_STARS_MEDIAN: int = 50
_FOLLOWERS_MEDIAN: int = 10

_COMMITS_WEIGHT: int = 2
_PRS_WEIGHT: int = 3
_ISSUES_WEIGHT: int = 1
_REVIEWS_WEIGHT: int = 1
_STARS_WEIGHT: int = 4
_FOLLOWERS_WEIGHT: int = 1
_TOTAL_WEIGHT: int = (
    _COMMITS_WEIGHT
    + _PRS_WEIGHT
    + _ISSUES_WEIGHT
    + _REVIEWS_WEIGHT
    + _STARS_WEIGHT
    + _FOLLOWERS_WEIGHT
)

_THRESHOLDS: tuple[float, ...] = (1.0, 12.5, 25.0, 37.5, 50.0, 62.5, 75.0, 87.5)
_LEVELS: tuple[str, ...] = ("S", "A+", "A", "A-", "B+", "B", "C+", "C")


@dataclass(frozen=True)
class GradeResult:
    """Result of a grade calculation."""

    letter: str
    percentile: float


def _exponential_cdf(x: float) -> float:
    """Return ``1 - 2 ** -x``. Ranges from 0 (x=0) to 1 (x=infinity)."""
    return float(1.0 - 2.0 ** (-x))


def _log_normal_cdf(x: float) -> float:
    """Return ``x / (1 + x)``. Pareto-style approximation. Ranges from 0 to 1."""
    return x / (1.0 + x)


def calculate_rank(
    *,
    commits: int,
    prs: int,
    issues: int,
    reviews: int,
    stars: int,
    followers: int,
) -> GradeResult:
    """Compute the percentile and letter grade.

    Args:
        commits: Total commit contributions in the rolling year window.
        prs: Total pull request contributions in the rolling year window.
        issues: Total issue contributions in the rolling year window.
        reviews: Total review contributions in the rolling year window.
        stars: Total stars across owned non-fork repositories.
        followers: Total followers.

    Returns:
        ``GradeResult`` with the letter and percentile (0..100, lower is better).
    """
    score: float = (
        _COMMITS_WEIGHT * _exponential_cdf(commits / _COMMITS_MEDIAN)
        + _PRS_WEIGHT * _exponential_cdf(prs / _PRS_MEDIAN)
        + _ISSUES_WEIGHT * _exponential_cdf(issues / _ISSUES_MEDIAN)
        + _REVIEWS_WEIGHT * _exponential_cdf(reviews / _REVIEWS_MEDIAN)
        + _STARS_WEIGHT * _log_normal_cdf(stars / _STARS_MEDIAN)
        + _FOLLOWERS_WEIGHT * _log_normal_cdf(followers / _FOLLOWERS_MEDIAN)
    )
    rank: float = 1.0 - score / _TOTAL_WEIGHT
    percentile: float = rank * 100.0
    for threshold, level in zip(_THRESHOLDS, _LEVELS, strict=True):
        if percentile <= threshold:
            return GradeResult(letter=level, percentile=percentile)
    return GradeResult(letter="C", percentile=percentile)
