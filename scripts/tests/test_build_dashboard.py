"""Tests for the unified dashboard build script."""

from typing import Any

from scripts.build_dashboard import compose_svg
from scripts.lib import dashboard_layout as dl


def _minimal_inputs() -> tuple[
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
]:
    return (
        {
            "bio": ["line one"],
            "trait_pills": [{"icon": "lightbulb", "label": "Solver"}],
        },
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
    assert f'viewBox="0 0 {dl.CANVAS_W} {dl.CANVAS_H}"' in svg
    assert svg.endswith("</svg>")


def test_compose_svg_preserves_uptime_marker() -> None:
    svg = compose_svg(*_minimal_inputs())
    assert "<!-- UPTIME_START -->1y<!-- UPTIME_END -->" in svg


def test_compose_svg_emits_every_stats_text_marker() -> None:
    svg = compose_svg(*_minimal_inputs())
    expected_text_keys: list[str] = [
        "STARS",
        "COMMITS",
        "PRS",
        "ISSUES",
        "CONTRIB_TO",
        "GRADE_LETTER",
        "TOTAL_CONTRIB",
        "TOTAL_CONTRIB_RANGE",
        "CURRENT_STREAK",
        "CURRENT_STREAK_RANGE",
        "LONGEST_STREAK",
        "LONGEST_STREAK_RANGE",
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


def test_compose_svg_animates_grade_ring_dashoffset() -> None:
    svg = compose_svg(*_minimal_inputs())
    grade_tag_start = svg.index('id="grade-ring"')
    next_close = svg.index(">", grade_tag_start)
    after_ring = svg[next_close : next_close + 600]
    assert "<animate " in after_ring
    assert 'attributeName="stroke-dashoffset"' in after_ring
    assert 'to="0"' in after_ring
    assert 'fill="freeze"' in after_ring


def test_compose_svg_keeps_grade_ring_static_dashoffset_zero() -> None:
    svg = compose_svg(*_minimal_inputs())
    grade_tag_start = svg.index('id="grade-ring"')
    grade_tag_end = svg.index(">", grade_tag_start)
    grade_tag = svg[grade_tag_start:grade_tag_end]
    assert 'stroke-dashoffset="0"' in grade_tag


def test_compose_svg_animates_grade_letter_group() -> None:
    svg = compose_svg(*_minimal_inputs())
    letter_marker = "<!-- GRADE_LETTER_START -->"
    idx = svg.index(letter_marker)
    surrounding = svg[max(0, idx - 400) : idx + 400]
    assert "<g" in surrounding
    assert 'attributeName="opacity"' in surrounding


def test_compose_svg_animates_streak_ring_dashoffset() -> None:
    svg = compose_svg(*_minimal_inputs())
    streak_tag_start = svg.index('id="streak-ring"')
    next_close = svg.index(">", streak_tag_start)
    after_ring = svg[next_close : next_close + 600]
    assert 'attributeName="stroke-dashoffset"' in after_ring
    assert 'to="0"' in after_ring


def test_compose_svg_keeps_streak_ring_static_dashoffset_zero() -> None:
    svg = compose_svg(*_minimal_inputs())
    streak_tag_start = svg.index('id="streak-ring"')
    streak_tag_end = svg.index(">", streak_tag_start)
    streak_tag = svg[streak_tag_start:streak_tag_end]
    assert 'stroke-dashoffset="0"' in streak_tag


def test_compose_svg_animates_total_contrib_number() -> None:
    svg = compose_svg(*_minimal_inputs())
    idx = svg.index("<!-- TOTAL_CONTRIB_START -->")
    surrounding = svg[max(0, idx - 400) : idx + 400]
    assert 'attributeName="opacity"' in surrounding


def test_compose_svg_animates_streak_numbers() -> None:
    svg = compose_svg(*_minimal_inputs())
    for marker in ("CURRENT_STREAK", "LONGEST_STREAK"):
        idx = svg.index(f"<!-- {marker}_START -->")
        surrounding = svg[max(0, idx - 400) : idx + 400]
        assert 'attributeName="opacity"' in surrounding, f"missing opacity for {marker}"


def test_compose_svg_wraps_each_lang_bar_in_animated_group() -> None:
    svg = compose_svg(*_minimal_inputs())
    for index in range(1, 6):
        bar_marker = f'id="lang-{index}-bar"'
        bar_idx = svg.index(bar_marker)
        surrounding = svg[max(0, bar_idx - 300) : bar_idx + 600]
        assert "<animateTransform " in surrounding, (
            f"lang-{index}-bar missing transform animation"
        )
        assert 'type="scale"' in surrounding
        assert 'from="0 1"' in surrounding
        assert 'to="1 1"' in surrounding


def test_compose_svg_keeps_lang_bars_patchable_by_id() -> None:
    svg = compose_svg(*_minimal_inputs())
    for index in range(1, 6):
        assert f'id="lang-{index}-bar"' in svg
        bar_idx = svg.index(f'id="lang-{index}-bar"')
        next_close = svg.index("/>", bar_idx)
        bar_tag = svg[bar_idx:next_close]
        assert ' width="' in bar_tag, (
            f"lang-{index}-bar must keep a width attribute for patching"
        )


def test_compose_svg_wraps_tech_icons_in_animated_groups() -> None:
    inputs = list(_minimal_inputs())
    inputs[2] = {
        "icons": [
            {"file": "python.svg", "label": "Python"},
            {"file": "python.svg", "label": "Rust"},
            {"file": "python.svg", "label": "Go"},
        ]
    }
    svg = compose_svg(*inputs)
    # Section headers are outlined paths, not raw text — anchor on the first label.
    first_label_idx = svg.index(">Python<")
    last_label_idx = svg.index(">Go<")
    tech_section = svg[first_label_idx - 5000 : last_label_idx + 5000]
    assert tech_section.count('attributeName="opacity"') >= 3, (
        "expected one opacity animation per tech icon group"
    )


def test_compose_svg_pulses_name_prompt_cursor() -> None:
    svg = compose_svg(*_minimal_inputs())
    assert 'repeatCount="indefinite"' in svg


def test_compose_svg_pulses_brain_image_when_present() -> None:
    svg = compose_svg(*_minimal_inputs())
    brain_token = 'opacity="0.3" href="data:image/png'  # noqa: S105
    if brain_token not in svg:
        return
    brain_idx = svg.index(brain_token)
    surrounding = svg[max(0, brain_idx - 600) : brain_idx + 200]
    assert 'repeatCount="indefinite"' in surrounding
    assert "0.3;0.42;0.3" in surrounding


def test_compose_svg_glows_quote_glyph() -> None:
    svg = compose_svg(*_minimal_inputs())
    rotate_idx = svg.index("rotate(180")
    surrounding = svg[max(0, rotate_idx - 200) : rotate_idx + 800]
    assert 'repeatCount="indefinite"' in surrounding


def test_compose_svg_emits_boot_pulse_on_name_prompt() -> None:
    svg = compose_svg(*_minimal_inputs())
    # The prompt is rendered as outlined path data, so anchor near the name
    # outlined glyph data via the role line tspans which ARE raw text.
    role_idx = svg.index("AI Engineer")
    surrounding = svg[max(0, role_idx - 4000) : role_idx + 200]
    boot_pulse_count = surrounding.count('attributeName="opacity"')
    assert boot_pulse_count >= 1, (
        "expected at least one opacity animation in the prompt area"
    )
    # The prompt group must carry both a freeze (boot) and indefinite (idle) animation
    assert 'fill="freeze"' in surrounding
    assert 'repeatCount="indefinite"' in surrounding
