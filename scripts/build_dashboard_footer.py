"""Build the static footer SVG for the GitHub profile dashboard.

Reads ``content/enjoy.yml``, composes the WHAT I ENJOY section + the
closing tagline, and writes the result to ``assets/dashboard-footer.svg``.

Run manually when content changes. Not part of the daily Action.
"""

import re
import sys
from pathlib import Path
from typing import Any

import yaml

from scripts.lib.text_to_path import outline

REPO_ROOT: Path = Path(__file__).resolve().parent.parent
CONTENT_DIR: Path = REPO_ROOT / "content"
UI_ICONS_DIR: Path = REPO_ROOT / "assets" / "icons" / "ui"
OUTPUT_PATH: Path = REPO_ROOT / "assets" / "dashboard-footer.svg"
INTER_BOLD: Path = REPO_ROOT / "scripts" / "fonts" / "Inter" / "Inter-Bold.otf"
INTER_MEDIUM: Path = REPO_ROOT / "scripts" / "fonts" / "Inter" / "Inter-Medium.otf"

ACCENT: str = "#9EFF5A"
ACCENT_DIM: str = "#6BBF3D"
TEXT: str = "#E8E8E0"
TEXT_MUTED: str = "#8B92A5"
BG: str = "#0A0E1A"


_INHERITABLE_ICON_ATTRS: tuple[str, ...] = (
    "fill",
    "stroke",
    "stroke-width",
    "stroke-linecap",
    "stroke-linejoin",
)


def _embed_icon(icon_path: Path, x: int, y: int, size: int) -> str:
    """Inline an icon SVG's contents into a translate+scale group.

    Mirrors :func:`scripts.build_dashboard_top.embed_icon`. Duplicated here
    to keep the footer build script independent of the top build script.
    Forwards the root ``<svg>``'s presentation attributes onto the wrapping
    ``<g>`` so Lucide-style outline icons render correctly after the outer
    element is stripped.
    """
    content: str = icon_path.read_text(encoding="utf-8")
    viewbox_match = re.search(r'viewBox\s*=\s*"([^"]+)"', content)
    if viewbox_match is None:
        msg = f"icon {icon_path.name} has no viewBox"
        raise ValueError(msg)
    parts = viewbox_match.group(1).split()
    source_size: float = max(float(parts[2]), float(parts[3]))
    scale: float = size / source_size

    root_match = re.match(r"<svg\b[^>]*>", content, re.DOTALL)
    if root_match is None:
        msg = f"icon {icon_path.name} has no <svg> root"
        raise ValueError(msg)
    inherited: list[str] = []
    for attr in _INHERITABLE_ICON_ATTRS:
        attr_match = re.search(
            rf'\s{re.escape(attr)}="([^"]*)"', root_match.group(0)
        )
        if attr_match is not None:
            inherited.append(f'{attr}="{attr_match.group(1)}"')

    inner_match = re.search(r"<svg[^>]*>(.*)</svg>", content, re.DOTALL)
    if inner_match is None:
        msg = f"icon {icon_path.name} has no closing </svg>"
        raise ValueError(msg)
    inner: str = inner_match.group(1).strip()
    inherited_attrs: str = (" " + " ".join(inherited)) if inherited else ""
    return (
        f'<g transform="translate({x},{y}) scale({scale:.4f})"'
        f'{inherited_attrs}>{inner}</g>'
    )


def render_enjoy_card(
    x: int,
    y: int,
    width: int,
    icon: str,
    title: str,
    description: list[str],
) -> str:
    """Render one of the four WHAT I ENJOY cards.

    Args:
        x: Card's left x.
        y: Card's top y.
        width: Card width.
        icon: UI icon filename (without ``.svg``).
        title: Card title (will be outlined).
        description: List of description lines (mono).

    Returns:
        An SVG fragment for the card (no wrapping group).
    """
    parts: list[str] = []
    icon_path: Path = UI_ICONS_DIR / f"{icon}.svg"
    parts.append(_embed_icon(icon_path, x=x, y=y, size=24))
    title_d: str = outline(title, INTER_BOLD, size_px=18)
    parts.append(
        f'<g transform="translate({x + 36},{y + 18})" fill="{ACCENT}">'
        f'<path d="{title_d}"/>'
        f'</g>'
    )
    for line_index, line in enumerate(description):
        line_y: int = y + 50 + line_index * 18
        parts.append(
            f'<text x="{x}" y="{line_y}" font-family="monospace" '
            f'font-size="12" fill="{TEXT_MUTED}">{line}</text>'
        )
    return "".join(parts)


def dotted_line(y: int, count: int, x_start: int, x_end: int) -> str:
    """Render a row of dim-lime dots.

    Args:
        y: y coordinate of all dots.
        count: number of dots.
        x_start: leftmost x.
        x_end: rightmost x.

    Returns:
        An SVG fragment of ``<circle>`` elements.
    """
    spacing: float = (x_end - x_start) / max(count - 1, 1)
    parts: list[str] = [
        f'<circle cx="{round(x_start + index * spacing)}" cy="{y}" r="1" fill="{ACCENT_DIM}"/>'
        for index in range(count)
    ]
    return "".join(parts)


def compose_svg(enjoy: dict[str, Any]) -> str:
    """Compose the full footer SVG.

    Args:
        enjoy: Parsed ``content/enjoy.yml``.

    Returns:
        A complete SVG document string.
    """
    parts: list[str] = []
    parts.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1500 280">')
    parts.append(f'<rect x="0" y="0" width="1500" height="280" fill="{BG}"/>')

    parts.append(_embed_icon(UI_ICONS_DIR / "heart.svg", x=30, y=42, size=20))
    header_d: str = outline("WHAT I ENJOY", INTER_BOLD, size_px=14)
    parts.append(
        f'<g transform="translate(58,58)" fill="{ACCENT}">'
        f'<path d="{header_d}"/>'
        f'</g>'
    )

    cards: list[dict[str, Any]] = enjoy.get("cards", [])
    if cards:
        column_width: int = (1500 - 60) // len(cards)
        for index, card in enumerate(cards):
            card_x: int = 30 + index * column_width
            parts.append(
                render_enjoy_card(
                    x=card_x,
                    y=100,
                    width=column_width - 20,
                    icon=card["icon"],
                    title=card["title"],
                    description=card["description"],
                )
            )

    parts.append(dotted_line(y=235, count=80, x_start=30, x_end=1470))

    closing: str = (
        f'<text x="750" y="270" font-family="monospace" font-size="13" '
        f'fill="{TEXT_MUTED}" text-anchor="middle">'
        f'<tspan>Thanks for stopping by! Let’s </tspan>'
        f'<tspan fill="{ACCENT}">build</tspan>'
        f'<tspan> </tspan>'
        f'<tspan fill="{ACCENT}">the</tspan>'
        f'<tspan> </tspan>'
        f'<tspan fill="{ACCENT}">future</tspan>'
        f'<tspan> together.</tspan>'
        f'</text>'
    )
    parts.append(closing)
    parts.append("</svg>")
    return "".join(parts)


def main() -> int:
    """Read enjoy YAML, compose footer SVG, write output."""
    try:
        enjoy = yaml.safe_load((CONTENT_DIR / "enjoy.yml").read_text(encoding="utf-8"))
        svg = compose_svg(enjoy)
        OUTPUT_PATH.write_text(svg, encoding="utf-8")
    except (FileNotFoundError, ValueError, yaml.YAMLError) as exc:
        sys.stderr.write(f"build_dashboard_footer: {exc}\n")
        return 1
    sys.stdout.write(f"build_dashboard_footer: wrote {OUTPUT_PATH}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
