"""Tests for the dashboard runner."""

from pathlib import Path
from typing import Any

import pytest

from scripts import update_dashboard
from scripts.update_dashboard import Source, run


class _Stub:
    def __init__(self, **kw: Any) -> None:
        for k, v in kw.items():
            setattr(self, k, v)


def _good_results() -> dict[str, Any]:
    return {
        "github_stats": _Stub(
            stars_display="116", commits_display="3.8k", prs_display="818",
            issues_display="36", contributed_to_display="3",
            stars=116, commits=3800, prs=818, issues=36, reviews=10, followers=20,
        ),
        "grade": _Stub(letter="A", percentile=25.0),
        "github_contrib": _Stub(
            total_count=5_981, total_display="5,981",
            total_range_label="Jan 1, 2026 - Present",
            current_streak_days=85, current_streak_range_label="Jan 31 - Apr 25",
            longest_streak_days=85, longest_streak_range_label="Jan 31 - Apr 25",
        ),
        "wakatime": _Stub(
            languages=[
                _Stub(name="Python", text="30 hrs", total_seconds=108_000.0),
                _Stub(name="Other", text="9 hrs 35 mins", total_seconds=34_500.0),
                _Stub(name="JavaScript", text="3 hrs 9 mins", total_seconds=11_340.0),
                _Stub(name="YAML", text="1 hr 25 mins", total_seconds=5_100.0),
                _Stub(name="Bash", text="1 hr 24 mins", total_seconds=5_040.0),
            ]
        ),
        "uptime": _Stub(value="2 years, 7 months"),
    }


def _real_svg_path(repo_root: Path) -> Path:
    return repo_root / "assets" / "dashboard.svg"


def _copy_svg(repo_root: Path, tmp_path: Path) -> Path:
    src = _real_svg_path(repo_root)
    dst = tmp_path / "dashboard.svg"
    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    return dst


def _all_good_sources(results: dict[str, Any]) -> list[Source]:
    return [
        Source("uptime", lambda: results["uptime"]),
        Source("github_stats", lambda: results["github_stats"]),
        Source("github_contrib", lambda: results["github_contrib"]),
        Source("wakatime", lambda: results["wakatime"]),
    ]


def test_run_applies_all_patches_when_every_source_succeeds(repo_root: Path, tmp_path: Path) -> None:
    svg = _copy_svg(repo_root, tmp_path)
    results = _good_results()
    exit_code = run(svg_path=svg, sources=_all_good_sources(results))
    content = svg.read_text(encoding="utf-8")
    assert exit_code == 0
    assert "<!-- STARS_START -->116<!-- STARS_END -->" in content
    assert "<!-- LANG_1_NAME_START -->Python<!-- LANG_1_NAME_END -->" in content
    assert "<!-- UPTIME_START -->2 years, 7 months<!-- UPTIME_END -->" in content


def test_run_skips_failed_source_patches_keeps_others(repo_root: Path, tmp_path: Path) -> None:
    svg = _copy_svg(repo_root, tmp_path)
    results = _good_results()

    def boom() -> Any:
        raise RuntimeError("wakatime down")

    sources: list[Source] = [
        Source("uptime", lambda: results["uptime"]),
        Source("github_stats", lambda: results["github_stats"]),
        Source("github_contrib", lambda: results["github_contrib"]),
        Source("wakatime", boom),
    ]
    pre = svg.read_text(encoding="utf-8")
    exit_code = run(svg_path=svg, sources=sources)
    post = svg.read_text(encoding="utf-8")
    assert exit_code == 0
    assert "<!-- STARS_START -->116<!-- STARS_END -->" in post
    pre_lang_value = pre.split("LANG_1_NAME_START -->")[1].split("<!-- LANG_1_NAME_END")[0]
    post_lang_value = post.split("LANG_1_NAME_START -->")[1].split("<!-- LANG_1_NAME_END")[0]
    assert post_lang_value == pre_lang_value


def test_run_returns_one_when_all_sources_fail(repo_root: Path, tmp_path: Path) -> None:
    svg = _copy_svg(repo_root, tmp_path)

    def boom() -> Any:
        raise RuntimeError("everything is broken")

    sources: list[Source] = [
        Source("uptime", boom),
        Source("github_stats", boom),
        Source("github_contrib", boom),
        Source("wakatime", boom),
    ]
    pre = svg.read_text(encoding="utf-8")
    exit_code = run(svg_path=svg, sources=sources)
    post = svg.read_text(encoding="utf-8")
    assert exit_code == 1
    assert pre == post


def test_run_does_not_rewrite_when_values_already_match(repo_root: Path, tmp_path: Path) -> None:
    svg = _copy_svg(repo_root, tmp_path)
    results = _good_results()
    run(svg_path=svg, sources=_all_good_sources(results))
    mtime_before = svg.stat().st_mtime_ns
    run(svg_path=svg, sources=_all_good_sources(results))
    assert svg.stat().st_mtime_ns == mtime_before
