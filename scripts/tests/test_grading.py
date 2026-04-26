"""Tests for the grading module."""

import pytest

from scripts.lib.grading import GradeResult, calculate_rank


def test_zero_user_lands_in_c_bucket() -> None:
    result = calculate_rank(commits=0, prs=0, issues=0, reviews=0, stars=0, followers=0)
    assert result.letter == "C"
    assert result.percentile == pytest.approx(100.0)


def test_at_median_user_lands_in_a_or_b() -> None:
    result = calculate_rank(commits=1000, prs=50, issues=25, reviews=2, stars=50, followers=10)
    assert result.letter in {"A-", "B+"}
    assert 25.0 <= result.percentile <= 50.0


def test_high_performer_lands_in_a_plus_or_better() -> None:
    result = calculate_rank(commits=10_000, prs=500, issues=200, reviews=50, stars=5_000, followers=500)
    assert result.letter in {"S", "A+"}
    assert result.percentile <= 12.5


def test_dineshs_current_stats_land_in_a_bucket() -> None:
    result = calculate_rank(commits=3800, prs=818, issues=36, reviews=10, stars=116, followers=20)
    assert result.letter in {"S", "A+", "A"}
    assert result.percentile <= 25.0


def test_letter_thresholds_are_inclusive_at_boundary() -> None:
    s_result = calculate_rank(commits=10**9, prs=10**9, issues=10**9, reviews=10**9, stars=10**9, followers=10**9)
    assert s_result.letter == "S"
    assert s_result.percentile == pytest.approx(0.0, abs=1e-5)


def test_increasing_commits_never_worsens_percentile() -> None:
    base = calculate_rank(commits=100, prs=0, issues=0, reviews=0, stars=0, followers=0)
    higher = calculate_rank(commits=10_000, prs=0, issues=0, reviews=0, stars=0, followers=0)
    assert higher.percentile <= base.percentile


def test_increasing_stars_never_worsens_percentile() -> None:
    base = calculate_rank(commits=0, prs=0, issues=0, reviews=0, stars=10, followers=0)
    higher = calculate_rank(commits=0, prs=0, issues=0, reviews=0, stars=10_000, followers=0)
    assert higher.percentile <= base.percentile


def test_returns_grade_result_dataclass() -> None:
    result = calculate_rank(commits=1000, prs=50, issues=25, reviews=2, stars=50, followers=10)
    assert isinstance(result, GradeResult)
    assert hasattr(result, "letter")
    assert hasattr(result, "percentile")
