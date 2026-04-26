"""Build the unified GitHub profile dashboard SVG.

Composes a single 1500x1000 canvas with one outer rounded frame, a left
sidebar of four cards (portrait / quote / connect / CTA), and a right
column of four sections (top panel / tech strip / stats row / enjoy
strip). Reads content from ``content/*.yml`` and writes the result to
``assets/dashboard.svg``.

Run manually when content changes. The daily Action only patches
marker-bounded values inside the produced SVG.
"""

import base64
import sys
from pathlib import Path
from typing import Any

import yaml

from scripts.lib import dashboard_layout as L
from scripts.lib.svg_primitives import embed_icon
from scripts.lib.text_to_path import outline

REPO_ROOT: Path = Path(__file__).resolve().parent.parent
CONTENT_DIR: Path = REPO_ROOT / "content"
ASSETS_DIR: Path = REPO_ROOT / "assets"
TECH_ICONS_DIR: Path = ASSETS_DIR / "icons" / "tech"
UI_ICONS_DIR: Path = ASSETS_DIR / "icons" / "ui"
PORTRAIT_PATH: Path = ASSETS_DIR / "portrait-card.png"
OUTPUT_PATH: Path = ASSETS_DIR / "dashboard.svg"
INTER_BOLD: Path = REPO_ROOT / "scripts" / "fonts" / "Inter" / "Inter-Bold.otf"
INTER_MEDIUM: Path = REPO_ROOT / "scripts" / "fonts" / "Inter" / "Inter-Medium.otf"


def _outlined_text(text: str, font: Path, size_px: int, x: int, y: int, fill: str) -> str:
    """Return a ``<g>`` containing ``text`` outlined as a path at (``x``, ``y``).

    The translation uses ``y`` as the baseline; outlined glyphs extend
    upward from that line per :func:`scripts.lib.text_to_path.outline`.
    """
    d: str = outline(text, font, size_px=size_px)
    return f'<g transform="translate({x},{y})" fill="{fill}"><path d="{d}"/></g>'


def _section_header(text: str, x: int, y: int, icon: str | None = None) -> str:
    """Render a small lime section header with an optional leading icon.

    Args:
        text: Header text (uppercased by convention).
        x: Top-left x of the header (icon goes here when present).
        y: Header baseline y.
        icon: Optional UI icon filename without ``.svg`` extension.

    Returns:
        An SVG fragment containing the icon (if any) plus the outlined header.
    """
    parts: list[str] = []
    text_x: int = x
    if icon is not None:
        parts.append(embed_icon(UI_ICONS_DIR / f"{icon}.svg", x=x, y=y - 13, size=15))
        text_x = x + 22
    parts.append(_outlined_text(text, INTER_BOLD, size_px=13, x=text_x, y=y, fill=L.ACCENT))
    return "".join(parts)


def _portrait_card() -> str:
    """Render the sidebar portrait card.

    Layout: photo inset 20px from card edges in upper region, ``Building``
    badge in the photo's top-right, name (outlined Inter Bold) and role
    line (lime mono) below the photo.
    """
    parts: list[str] = []
    card: L.Rect = L.PORTRAIT_CARD
    photo_pad: int = 16
    photo_x: int = card.x + photo_pad
    photo_y: int = card.y + photo_pad
    photo_w: int = card.w - 2 * photo_pad
    photo_h: int = 290

    if PORTRAIT_PATH.exists():
        b64: str = base64.b64encode(PORTRAIT_PATH.read_bytes()).decode("ascii")
        parts.append(
            f'<image x="{photo_x}" y="{photo_y}" width="{photo_w}" height="{photo_h}" '
            f'href="data:image/png;base64,{b64}" preserveAspectRatio="xMidYMid slice"/>'
        )
    else:
        parts.append(
            f'<rect x="{photo_x}" y="{photo_y}" width="{photo_w}" height="{photo_h}" '
            f'fill="{L.SURFACE_2}" stroke="{L.BORDER}"/>'
        )

    badge_w: int = 88
    badge_h: int = 24
    badge_x: int = photo_x + photo_w - badge_w - 10
    badge_y: int = photo_y + 10
    parts.append(
        f'<rect x="{badge_x}" y="{badge_y}" width="{badge_w}" height="{badge_h}" '
        f'rx="12" fill="{L.BG}" fill-opacity="0.85" stroke="{L.ACCENT}"/>'
    )
    parts.append(
        f'<circle cx="{badge_x + 13}" cy="{badge_y + 12}" r="4" fill="{L.ACCENT}"/>'
    )
    parts.append(
        f'<text x="{badge_x + 24}" y="{badge_y + 16}" font-family="monospace" '
        f'font-size="11" fill="{L.TEXT}">Building</text>'
    )

    name_y: int = photo_y + photo_h + 32
    parts.append(
        _outlined_text(
            "Dinesh Dawonauth",
            INTER_BOLD,
            size_px=20,
            x=card.x + 20,
            y=name_y,
            fill=L.TEXT,
        )
    )
    role_y: int = name_y + 22
    parts.append(
        f'<text x="{card.x + 20}" y="{role_y}" font-family="monospace" '
        f'font-size="11" fill="{L.ACCENT}">'
        f'<tspan>&gt;_ </tspan>'
        f'<tspan fill="{L.TEXT_MUTED}">AI Engineer · Developer · Builder</tspan>'
        f'</text>'
    )
    return "".join(parts)


def _quote_card() -> str:
    """Render the sidebar quote card."""
    parts: list[str] = []
    card: L.Rect = L.QUOTE_CARD
    bar_x: int = card.x + 16
    bar_y: int = card.y + 22
    parts.append(
        f'<rect x="{bar_x}" y="{bar_y}" width="3" height="{card.h - 44}" '
        f'fill="{L.ACCENT}"/>'
    )
    text_x: int = bar_x + 16
    line1_y: int = card.y + 44
    line2_y: int = line1_y + 22
    parts.append(
        f'<text x="{text_x}" y="{line1_y}" font-family="monospace" '
        f'font-size="12" fill="{L.TEXT_MUTED}">"Shipping love into</text>'
    )
    parts.append(
        f'<text x="{text_x}" y="{line2_y}" font-family="monospace" '
        f'font-size="12" fill="{L.TEXT_MUTED}">'
        f'<tspan>production since </tspan>'
        f'<tspan fill="{L.ACCENT}">2018</tspan>'
        f'<tspan>."</tspan>'
        f'</text>'
    )
    return "".join(parts)


def _connect_card(connect: dict[str, Any]) -> str:
    """Render the sidebar connect card with rows of icon + label."""
    parts: list[str] = []
    card: L.Rect = L.CONNECT_CARD
    parts.append(_section_header("CONNECT", x=card.x + 18, y=card.y + 28, icon="mail"))
    rows: list[dict[str, str]] = connect.get("rows", [])
    row_origin_y: int = card.y + 56
    row_stride: int = 28
    for index, row in enumerate(rows):
        row_y: int = row_origin_y + index * row_stride
        icon_path: Path = UI_ICONS_DIR / f"{row['icon']}.svg"
        parts.append(embed_icon(icon_path, x=card.x + 20, y=row_y - 12, size=14))
        parts.append(
            f'<text x="{card.x + 42}" y="{row_y}" font-family="monospace" '
            f'font-size="12" fill="{L.TEXT_MUTED}">{row["label"]}</text>'
        )
    return "".join(parts)


def _cta_card() -> str:
    """Render the sidebar CTA card with a multi-line build prompt."""
    parts: list[str] = []
    card: L.Rect = L.CTA_CARD
    parts.append(_section_header("LET'S BUILD", x=card.x + 18, y=card.y + 28, icon="sparkles"))
    body_x: int = card.x + 20
    line1_y: int = card.y + 70
    parts.append(
        _outlined_text(
            "Let's build something",
            INTER_BOLD,
            size_px=18,
            x=body_x,
            y=line1_y,
            fill=L.TEXT,
        )
    )
    line2_y: int = line1_y + 26
    parts.append(
        _outlined_text(
            "meaningful together.",
            INTER_BOLD,
            size_px=18,
            x=body_x,
            y=line2_y,
            fill=L.ACCENT,
        )
    )
    cursor_y: int = line2_y + 28
    parts.append(
        f'<text x="{body_x}" y="{cursor_y}" font-family="monospace" '
        f'font-size="12" fill="{L.TEXT_MUTED}">'
        f'<tspan fill="{L.ACCENT}">&gt; </tspan>'
        f'<tspan>open to collaborations</tspan>'
        f'</text>'
    )
    return "".join(parts)


def compose_svg(
    about: dict[str, Any],
    system_info: dict[str, Any],
    tech_stack: dict[str, Any],
    connect: dict[str, Any],
    enjoy: dict[str, Any],
) -> str:
    """Compose the entire dashboard SVG as a single string.

    Args:
        about: Parsed ``content/about.yml``.
        system_info: Parsed ``content/system_info.yml``.
        tech_stack: Parsed ``content/tech_stack.yml``.
        connect: Parsed ``content/connect.yml``.
        enjoy: Parsed ``content/enjoy.yml``.

    Returns:
        A complete SVG document string.
    """
    parts: list[str] = []
    parts.append(L.svg_open())
    parts.append(L.canvas_background())
    parts.append(L.outer_frame())

    parts.append(L.panel(L.PORTRAIT_CARD))
    parts.append(_portrait_card())
    parts.append(L.panel(L.QUOTE_CARD))
    parts.append(_quote_card())
    parts.append(L.panel(L.CONNECT_CARD))
    parts.append(_connect_card(connect))
    parts.append(L.panel(L.CTA_CARD))
    parts.append(_cta_card())

    parts.append(L.panel(L.TOP_PANEL))
    parts.append(L.panel(L.TECH_PANEL))
    parts.append(L.panel(L.STATS_GLANCE))
    parts.append(L.panel(L.STATS_CONTRIB))
    parts.append(L.panel(L.STATS_LANGS))
    parts.append(L.panel(L.ENJOY_PANEL))

    parts.append("</svg>")
    return "".join(parts)


def _read_yaml(path: Path) -> dict[str, Any]:
    """Read and parse a YAML file."""
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def main() -> int:
    """Read content YAMLs, compose the SVG, write to disk."""
    try:
        about = _read_yaml(CONTENT_DIR / "about.yml")
        system_info = _read_yaml(CONTENT_DIR / "system_info.yml")
        tech_stack = _read_yaml(CONTENT_DIR / "tech_stack.yml")
        connect = _read_yaml(CONTENT_DIR / "connect.yml")
        enjoy = _read_yaml(CONTENT_DIR / "enjoy.yml")
        svg = compose_svg(about, system_info, tech_stack, connect, enjoy)
        OUTPUT_PATH.write_text(svg, encoding="utf-8")
    except (FileNotFoundError, ValueError, yaml.YAMLError) as exc:
        sys.stderr.write(f"build_dashboard: {exc}\n")
        return 1
    sys.stdout.write(f"build_dashboard: wrote {OUTPUT_PATH}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
