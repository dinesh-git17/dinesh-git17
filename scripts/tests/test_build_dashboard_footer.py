"""Tests for the dashboard-footer build script."""

from scripts.build_dashboard_footer import compose_svg, render_enjoy_card, dotted_line


def test_compose_svg_returns_complete_svg_with_four_cards() -> None:
    enjoy = {"cards": [
        {"icon": "box",          "title": "Building",  "description": ["a", "b"]},
        {"icon": "notebook-pen", "title": "Writing",   "description": ["c", "d"]},
        {"icon": "telescope",    "title": "Exploring", "description": ["e", "f"]},
        {"icon": "lightbulb",    "title": "Thinking",  "description": ["g", "h"]},
    ]}
    svg = compose_svg(enjoy)
    assert svg.startswith('<svg')
    assert 'viewBox="0 0 1500 280"' in svg
    assert svg.count("<g transform=\"translate(") >= 4
    assert "Thanks for stopping by" in svg
    assert "</svg>" in svg


def test_dotted_line_renders_circles() -> None:
    line = dotted_line(y=235, count=20, x_start=0, x_end=1500)
    assert line.count("<circle") == 20


def test_render_enjoy_card_includes_title_and_description() -> None:
    card = render_enjoy_card(
        x=30,
        y=100,
        width=350,
        icon="box",
        title="Building",
        description=["line one", "line two"],
    )
    assert "line one" in card
    assert "line two" in card
