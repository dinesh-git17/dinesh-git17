"""Tests for the unified dashboard build script."""

from pathlib import Path

from scripts.build_dashboard import compose_svg
from scripts.lib import dashboard_layout as L


def _minimal_inputs() -> tuple[dict, dict, dict, dict, dict]:
    return (
        {"bio": ["line one"], "trait_pills": [{"icon": "lightbulb", "label": "Solver"}]},
        {
            "rows": [
                {
                    "icon": "clock",
                    "label": "Uptime",
                    "value": "<!-- UPTIME_START -->1y<!-- UPTIME_END -->",
                }
            ]
        },
        {"icons": [{"file": "python.svg", "label": "Python"}]},
        {"rows": [{"icon": "mail", "label": "info@dineshd.dev", "href": ""}]},
        {
            "cards": [
                {"icon": "box", "title": "Building", "description": ["a", "b"]},
                {"icon": "notebook-pen", "title": "Writing", "description": ["c", "d"]},
                {"icon": "telescope", "title": "Exploring", "description": ["e", "f"]},
                {"icon": "lightbulb", "title": "Thinking", "description": ["g", "h"]},
            ]
        },
    )


def test_compose_svg_returns_complete_document() -> None:
    svg = compose_svg(*_minimal_inputs())
    assert svg.startswith("<svg")
    assert f'viewBox="0 0 {L.CANVAS_W} {L.CANVAS_H}"' in svg
    assert svg.endswith("</svg>")


def test_compose_svg_preserves_uptime_marker() -> None:
    svg = compose_svg(*_minimal_inputs())
    assert "<!-- UPTIME_START -->1y<!-- UPTIME_END -->" in svg


def test_compose_svg_emits_every_stats_text_marker() -> None:
    svg = compose_svg(*_minimal_inputs())
    expected_text_keys: list[str] = [
        "STARS", "COMMITS", "PRS", "ISSUES", "CONTRIB_TO",
        "GRADE_LETTER",
        "TOTAL_CONTRIB", "TOTAL_CONTRIB_RANGE",
        "CURRENT_STREAK", "CURRENT_STREAK_RANGE",
        "LONGEST_STREAK", "LONGEST_STREAK_RANGE",
    ]
    for key in expected_text_keys:
        assert f"<!-- {key}_START -->" in svg, f"missing {key}_START marker"
        assert f"<!-- {key}_END -->" in svg, f"missing {key}_END marker"
    for index in range(1, 6):
        assert f"<!-- LANG_{index}_NAME_START -->" in svg
        assert f"<!-- LANG_{index}_VALUE_START -->" in svg


def test_compose_svg_emits_id_anchored_attribute_targets() -> None:
    svg = compose_svg(*_minimal_inputs())
    assert 'id="grade-ring"' in svg
    assert 'id="streak-ring"' in svg
    for index in range(1, 6):
        assert f'id="lang-{index}-bar"' in svg


def test_compose_svg_renders_all_section_panels() -> None:
    svg = compose_svg(*_minimal_inputs())
    assert "ABOUT ME" not in svg
    assert "SYSTEM INFO" not in svg
    assert "TECH I WORK WITH" not in svg
    assert "GITHUB AT A GLANCE" not in svg
    assert "CONTRIBUTION OVERVIEW" not in svg
    assert "TOP LANGUAGES" not in svg
    assert "WHAT I ENJOY" not in svg
    assert "Thanks for stopping by" in svg
