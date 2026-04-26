"""Tests for the dashboard-top build script."""

from pathlib import Path

import pytest

from scripts.build_dashboard_top import (
    canada_flag,
    compose_svg,
    embed_icon,
    label_value_row,
)

REPO_ROOT_FIXTURE = Path(__file__).resolve().parent.parent.parent / "assets" / "icons"


def test_embed_icon_inlines_svg_content(tmp_path: Path) -> None:
    icon = tmp_path / "test.svg"
    icon.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
        '<path stroke="#9EFF5A" d="M3 12l9-9 9 9"/></svg>',
        encoding="utf-8",
    )
    inlined = embed_icon(icon, x=100, y=200, size=20)
    assert '<g transform="translate(100,200) scale(' in inlined
    assert '<path stroke="#9EFF5A" d="M3 12l9-9 9 9"/>' in inlined
    assert "<svg" not in inlined  # outer svg stripped, inner content kept


def test_label_value_row_renders_icon_label_value() -> None:
    icon_path = REPO_ROOT_FIXTURE / "ui" / "clock.svg"
    row = label_value_row(
        icon_path=icon_path,
        x=100,
        y=200,
        label="Uptime",
        value="2 years, 7 months",
    )
    assert "Uptime" in row
    assert "2 years, 7 months" in row
    assert 'fill="#9EFF5A"' in row  # label rendered in lime


def test_canada_flag_renders_three_rects() -> None:
    flag = canada_flag(x=300, y=200, width=18, height=12)
    flag_upper = flag.upper()
    assert flag.count("<rect") == 3
    assert 'FILL="#FF0000"' in flag_upper or 'FILL="#D52B1E"' in flag_upper
    assert 'FILL="#FFFFFF"' in flag_upper or 'fill="white"' in flag.lower()


def test_compose_svg_returns_complete_svg_with_all_panels() -> None:
    svg = compose_svg(
        about={"bio": ["line one"], "trait_pills": []},
        system_info={
            "rows": [
                {
                    "icon": "clock",
                    "label": "Uptime",
                    "value": "<!-- UPTIME_START -->1y<!-- UPTIME_END -->",
                }
            ]
        },
        tech_stack={"icons": []},
        connect={"rows": []},
    )
    assert svg.startswith("<svg")
    assert 'viewBox="0 0 1500 880"' in svg
    assert "Dinesh Dawonauth" not in svg  # outlined as path, not as text
    assert "<!-- UPTIME_START -->1y<!-- UPTIME_END -->" in svg
    assert "</svg>" in svg
