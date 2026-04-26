"""Live dashboard runner: fetch sources, patch the SVG, soft-fail per source.

Invoked by ``.github/workflows/update-profile.yml`` on a six-hour cron and
on manual ``workflow_dispatch``. Reads ``GH_USER_LOGIN``,
``READMEDASH_TOKEN``, and ``WAKATIME_API_KEY`` from the environment.
"""

import os
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.lib import grading, patches, svg_markers
from scripts.lib.sources import github_contrib, github_stats, uptime, wakatime

REPO_ROOT: Path = Path(__file__).resolve().parent.parent
DEFAULT_SVG_PATH: Path = REPO_ROOT / "assets" / "dashboard.svg"


@dataclass(frozen=True)
class Source:
    """One named, lazily-fetched data source."""

    name: str
    fetch: Callable[[], Any]


def _build_default_sources() -> list[Source]:
    """Wire the production sources from environment variables.

    ``grade`` is not a primary source. The runner derives it from
    ``github_stats`` after the fetch loop, so it succeeds or fails with
    its prerequisite.
    """
    login: str = os.environ["GH_USER_LOGIN"]
    gh_token: str = os.environ["READMEDASH_TOKEN"]
    waka_key: str | None = os.environ.get("WAKATIME_API_KEY") or None

    return [
        Source("uptime", uptime.fetch),
        Source("github_stats", lambda: github_stats.fetch(login=login, token=gh_token)),
        Source(
            "github_contrib", lambda: github_contrib.fetch(login=login, token=gh_token)
        ),
        Source(
            "wakatime", lambda: wakatime.fetch(username="dinbuilds", api_key=waka_key)
        ),
    ]


def _derive_grade(results: dict[str, Any]) -> None:
    """Add a ``"grade"`` key to ``results`` when ``"github_stats"`` is present."""
    stats = results.get("github_stats")
    if stats is None:
        return
    results["grade"] = grading.calculate_rank(
        commits=stats.commits,
        prs=stats.prs,
        issues=stats.issues,
        reviews=stats.reviews,
        stars=stats.stars,
        followers=stats.followers,
    )


def run(*, svg_path: Path, sources: list[Source]) -> int:
    """Fetch every source, walk the catalogue, apply patches, return an exit code.

    Returns 0 when at least one source succeeds; 1 when every source fails.
    """
    results: dict[str, Any] = {}
    failures: dict[str, Exception] = {}
    for source in sources:
        try:
            results[source.name] = source.fetch()
        except Exception as exc:
            failures[source.name] = exc
            sys.stderr.write(f"update_dashboard: source {source.name} failed: {exc}\n")

    _derive_grade(results)

    if not results:
        sys.stderr.write("update_dashboard: every source failed; SVG unchanged\n")
        return 1

    applied: int = 0
    for entry in patches.catalogue():
        if entry.source not in results:
            continue
        try:
            value: str = entry.value_fn(results)
        except Exception as exc:
            sys.stderr.write(
                f"update_dashboard: value_fn for {entry.target_id} raised: {exc}\n"
            )
            continue
        if entry.target_kind == "marker":
            svg_markers.patch_marker(svg_path, entry.target_id, value)
        else:
            if entry.attribute_name is None:
                msg = (
                    f"catalogue entry for {entry.target_id} "
                    f"has target_kind='attribute' but attribute_name is None"
                )
                raise RuntimeError(msg)
            svg_markers.patch_element_attribute(
                svg_path, entry.target_id, entry.attribute_name, value
            )
        applied += 1

    sys.stdout.write(
        f"update_dashboard: applied {applied} patches; "
        f"sources ok={list(results)} failed={list(failures)}\n"
    )
    return 0


def main() -> int:
    """Entry point invoked by the workflow."""
    sources = _build_default_sources()
    return run(svg_path=DEFAULT_SVG_PATH, sources=sources)


if __name__ == "__main__":
    raise SystemExit(main())
