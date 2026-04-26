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


def _canada_flag(x: int, y: int, width: int, height: int) -> str:
    """Render a small inline Canadian flag using three coloured rects."""
    side: int = round(width * 0.25)
    centre: int = width - 2 * side
    return (
        f'<rect x="{x}" y="{y}" width="{side}" height="{height}" fill="#D52B1E"/>'
        f'<rect x="{x + side}" y="{y}" width="{centre}" height="{height}" fill="#FFFFFF"/>'
        f'<rect x="{x + side + centre}" y="{y}" width="{side}" height="{height}" fill="#D52B1E"/>'
    )


def _top_panel(about: dict[str, Any], system_info: dict[str, Any]) -> str:
    """Render the top panel: ABOUT ME on the left, SYSTEM INFO on the right.

    A single shared panel split by a vertical divider running floor-to-ceiling
    inside the panel's inner padding.
    """
    parts: list[str] = []
    panel: L.Rect = L.TOP_PANEL
    inner_pad: int = 24
    divider_x: int = panel.cx
    parts.append(
        f'<line x1="{divider_x}" y1="{panel.y + inner_pad}" '
        f'x2="{divider_x}" y2="{panel.bottom - inner_pad}" '
        f'stroke="{L.BORDER}"/>'
    )

    about_x: int = panel.x + inner_pad
    parts.append(_section_header("ABOUT ME", x=about_x, y=panel.y + 36, icon="user"))
    bio_lines: list[str] = about.get("bio", [])
    bio_origin_y: int = panel.y + 72
    for index, line in enumerate(bio_lines):
        line_y: int = bio_origin_y + index * 22
        parts.append(
            f'<text x="{about_x}" y="{line_y}" font-family="monospace" '
            f'font-size="14" fill="{L.TEXT}">{line}</text>'
        )

    pills: list[dict[str, str]] = about.get("trait_pills", [])
    pill_origin_y: int = bio_origin_y + len(bio_lines) * 22 + 18
    pill_w: int = (divider_x - about_x - inner_pad - 12) // 2
    pill_h: int = 28
    pill_stride_x: int = pill_w + 12
    pill_stride_y: int = pill_h + 8
    for index, pill in enumerate(pills):
        col: int = index % 2
        row: int = index // 2
        px: int = about_x + col * pill_stride_x
        py: int = pill_origin_y + row * pill_stride_y
        parts.append(
            f'<rect x="{px}" y="{py}" width="{pill_w}" height="{pill_h}" '
            f'rx="14" fill="{L.SURFACE_2}" stroke="{L.BORDER}"/>'
        )
        parts.append(
            embed_icon(UI_ICONS_DIR / f"{pill['icon']}.svg", x=px + 10, y=py + 7, size=14)
        )
        parts.append(
            f'<text x="{px + 32}" y="{py + 19}" font-family="monospace" '
            f'font-size="12" fill="{L.TEXT}">{pill["label"]}</text>'
        )

    sys_x: int = divider_x + inner_pad
    parts.append(_section_header("SYSTEM INFO", x=sys_x, y=panel.y + 36, icon="hard-drive"))
    rows: list[dict[str, str]] = system_info.get("rows", [])
    row_origin_y: int = panel.y + 72
    row_stride: int = 22
    label_x: int = sys_x + 22
    value_right_x: int = panel.right - inner_pad
    for index, row in enumerate(rows):
        row_y: int = row_origin_y + index * row_stride
        icon_path: Path = UI_ICONS_DIR / f"{row['icon']}.svg"
        parts.append(embed_icon(icon_path, x=sys_x, y=row_y - 12, size=14))
        parts.append(
            f'<text x="{label_x}" y="{row_y}" font-family="monospace" '
            f'font-size="12" fill="{L.ACCENT}">{row["label"]}</text>'
        )
        if row.get("flag") == "CA":
            parts.append(_canada_flag(x=value_right_x - 18, y=row_y - 9, width=16, height=11))
            value_anchor_x: int = value_right_x - 24
        else:
            value_anchor_x = value_right_x
        parts.append(
            f'<text x="{value_anchor_x}" y="{row_y}" font-family="monospace" '
            f'font-size="12" fill="{L.TEXT}" text-anchor="end">{row["value"]}</text>'
        )
    return "".join(parts)


def _tech_strip(tech_stack: dict[str, Any]) -> str:
    """Render the TECH I WORK WITH strip panel.

    Header row at the top of the panel; below it, a single horizontal row
    of icons with a small label under each. Icons are evenly distributed
    across the panel's inner width.
    """
    parts: list[str] = []
    panel: L.Rect = L.TECH_PANEL
    inner_pad: int = 24
    parts.append(
        _section_header("TECH I WORK WITH", x=panel.x + inner_pad, y=panel.y + 36, icon="terminal")
    )
    icons: list[dict[str, str]] = tech_stack.get("icons", [])
    if not icons:
        return "".join(parts)
    icon_size: int = 48
    label_y: int = panel.bottom - 26
    icons_top: int = panel.y + 64
    inner_left: int = panel.x + inner_pad
    inner_w: int = panel.w - 2 * inner_pad
    column_w: float = inner_w / len(icons)
    for index, icon_info in enumerate(icons):
        slot_cx: float = inner_left + (index + 0.5) * column_w
        icon_x: float = slot_cx - icon_size / 2
        icon_path: Path = TECH_ICONS_DIR / icon_info["file"]
        parts.append(embed_icon(icon_path, x=icon_x, y=icons_top, size=icon_size))
        parts.append(
            f'<text x="{slot_cx:g}" y="{label_y}" font-family="monospace" '
            f'font-size="11" fill="{L.TEXT_MUTED}" text-anchor="middle">{icon_info["label"]}</text>'
        )
    return "".join(parts)


_GLANCE_ROWS: tuple[tuple[str, str, str], ...] = (
    ("Total Stars Earned",        "STARS",        "116"),
    ("Total Commits (last year)", "COMMITS",      "3.8k"),
    ("Total PRs",                 "PRS",          "818"),
    ("Total Issues",              "ISSUES",       "36"),
    ("Contributed to (last year)", "CONTRIB_TO",  "3"),
)

_LANG_ROWS: tuple[tuple[str, str, str, int, str], ...] = (
    ("LANG_1", "Python",     "30 hrs",         180, L.ACCENT),
    ("LANG_2", "Other",      "9 hrs 35 mins",   58, L.ACCENT_DIM),
    ("LANG_3", "JavaScript", "3 hrs 9 mins",    19, L.ACCENT_DIM),
    ("LANG_4", "YAML",       "1 hr 25 mins",     8, L.ACCENT_DIM),
    ("LANG_5", "Bash",       "1 hr 24 mins",     8, L.ACCENT_DIM),
)


def _stats_glance() -> str:
    """Render the GITHUB AT A GLANCE card with 5 metric rows + grade ring."""
    parts: list[str] = []
    card: L.Rect = L.STATS_GLANCE
    parts.append(
        _section_header("GITHUB AT A GLANCE", x=card.x + 20, y=card.y + 32, icon="bar-chart-3")
    )
    label_x: int = card.x + 20
    value_x: int = card.x + 240
    row_origin_y: int = card.y + 78
    row_stride: int = 28
    for index, (label, key, value) in enumerate(_GLANCE_ROWS):
        row_y: int = row_origin_y + index * row_stride
        parts.append(
            f'<text x="{label_x}" y="{row_y}" font-family="monospace" '
            f'font-size="12" fill="{L.TEXT}">{label}</text>'
        )
        parts.append(
            f'<text x="{value_x}" y="{row_y}" font-family="monospace" '
            f'font-size="12" fill="{L.ACCENT}" text-anchor="end">'
            f'<!-- {key}_START -->{value}<!-- {key}_END --></text>'
        )

    ring_cx: int = card.right - 60
    ring_cy: int = card.y + 158
    ring_r: int = 38
    ring_circumference: int = round(2 * 3.14159 * ring_r)
    parts.append(
        f'<circle cx="{ring_cx}" cy="{ring_cy}" r="{ring_r}" fill="none" '
        f'stroke="{L.TRACK}" stroke-width="6"/>'
    )
    parts.append(
        f'<circle id="grade-ring" cx="{ring_cx}" cy="{ring_cy}" r="{ring_r}" fill="none" '
        f'stroke="{L.ACCENT}" stroke-width="6" stroke-dasharray="180 {ring_circumference}" '
        f'stroke-dashoffset="0" transform="rotate(-90 {ring_cx} {ring_cy})" '
        f'stroke-linecap="round"/>'
    )
    parts.append(
        f'<text x="{ring_cx}" y="{ring_cy + 8}" font-family="monospace" font-size="24" '
        f'font-weight="bold" fill="{L.TEXT}" text-anchor="middle">'
        f'<!-- GRADE_LETTER_START -->A<!-- GRADE_LETTER_END --></text>'
    )
    parts.append(
        f'<text x="{ring_cx}" y="{ring_cy + 56}" font-family="monospace" font-size="11" '
        f'fill="{L.TEXT_MUTED}" text-anchor="middle">Overall Grade</text>'
    )
    return "".join(parts)


def _stats_contrib() -> str:
    """Render the CONTRIBUTION OVERVIEW card: total + current + longest streak."""
    parts: list[str] = []
    card: L.Rect = L.STATS_CONTRIB
    parts.append(
        _section_header("CONTRIBUTION OVERVIEW", x=card.x + 20, y=card.y + 32, icon="calendar")
    )
    col_w: int = card.w // 3
    col_centres: list[int] = [card.x + col_w // 2 + i * col_w for i in range(3)]

    total_cx: int = col_centres[0]
    parts.append(
        f'<text x="{total_cx}" y="{card.y + 130}" font-family="monospace" font-size="30" '
        f'font-weight="bold" fill="{L.TEXT}" text-anchor="middle">'
        f'<!-- TOTAL_CONTRIB_START -->5,981<!-- TOTAL_CONTRIB_END --></text>'
    )
    parts.append(
        f'<text x="{total_cx}" y="{card.y + 158}" font-family="monospace" font-size="11" '
        f'fill="{L.ACCENT}" text-anchor="middle">Total Contributions</text>'
    )
    parts.append(
        f'<text x="{total_cx}" y="{card.y + 178}" font-family="monospace" font-size="10" '
        f'fill="{L.TEXT_MUTED}" text-anchor="middle">'
        f'<!-- TOTAL_CONTRIB_RANGE_START -->Jan 1, 2025 - Present<!-- TOTAL_CONTRIB_RANGE_END --></text>'
    )

    streak_cx: int = col_centres[1]
    streak_cy: int = card.y + 130
    streak_r: int = 38
    streak_circumference: int = round(2 * 3.14159 * streak_r)
    parts.append(
        f'<circle cx="{streak_cx}" cy="{streak_cy}" r="{streak_r}" fill="none" '
        f'stroke="{L.TRACK}" stroke-width="6"/>'
    )
    parts.append(
        f'<circle id="streak-ring" cx="{streak_cx}" cy="{streak_cy}" r="{streak_r}" fill="none" '
        f'stroke="{L.ACCENT}" stroke-width="6" stroke-dasharray="{streak_circumference} {streak_circumference}" '
        f'stroke-dashoffset="0" transform="rotate(-90 {streak_cx} {streak_cy})" '
        f'stroke-linecap="round"/>'
    )
    parts.append(
        f'<text x="{streak_cx}" y="{streak_cy + 9}" font-family="monospace" font-size="26" '
        f'font-weight="bold" fill="{L.TEXT}" text-anchor="middle">'
        f'<!-- CURRENT_STREAK_START -->85<!-- CURRENT_STREAK_END --></text>'
    )
    parts.append(
        f'<text x="{streak_cx}" y="{card.y + 200}" font-family="monospace" font-size="11" '
        f'fill="{L.ACCENT}" text-anchor="middle">Current Streak</text>'
    )
    parts.append(
        f'<text x="{streak_cx}" y="{card.y + 220}" font-family="monospace" font-size="10" '
        f'fill="{L.TEXT_MUTED}" text-anchor="middle">'
        f'<!-- CURRENT_STREAK_RANGE_START -->Jan 31 - Apr 25<!-- CURRENT_STREAK_RANGE_END --></text>'
    )

    longest_cx: int = col_centres[2]
    parts.append(
        f'<text x="{longest_cx}" y="{card.y + 130}" font-family="monospace" font-size="30" '
        f'font-weight="bold" fill="{L.TEXT}" text-anchor="middle">'
        f'<!-- LONGEST_STREAK_START -->85<!-- LONGEST_STREAK_END --></text>'
    )
    parts.append(
        f'<text x="{longest_cx}" y="{card.y + 158}" font-family="monospace" font-size="11" '
        f'fill="{L.ACCENT}" text-anchor="middle">Longest Streak</text>'
    )
    parts.append(
        f'<text x="{longest_cx}" y="{card.y + 178}" font-family="monospace" font-size="10" '
        f'fill="{L.TEXT_MUTED}" text-anchor="middle">'
        f'<!-- LONGEST_STREAK_RANGE_START -->Jan 31 - Apr 25<!-- LONGEST_STREAK_RANGE_END --></text>'
    )
    return "".join(parts)


def _stats_langs() -> str:
    """Render the TOP LANGUAGES (BY HOURS) card with 5 bar rows + tracks."""
    parts: list[str] = []
    card: L.Rect = L.STATS_LANGS
    parts.append(
        _section_header("TOP LANGUAGES", x=card.x + 20, y=card.y + 32, icon="code-xml")
    )
    parts.append(
        f'<text x="{card.x + 20}" y="{card.y + 50}" font-family="monospace" '
        f'font-size="10" fill="{L.TEXT_MUTED}">(BY HOURS)</text>'
    )
    label_x: int = card.x + 20
    track_x: int = card.x + 96
    track_w: int = 184
    value_x: int = card.right - 20
    row_origin_y: int = card.y + 86
    row_stride: int = 36
    for index, (key, name, value, bar_w, bar_fill) in enumerate(_LANG_ROWS):
        row_y: int = row_origin_y + index * row_stride
        parts.append(
            f'<text x="{label_x}" y="{row_y + 10}" font-family="monospace" '
            f'font-size="12" fill="{L.TEXT}">'
            f'<!-- {key}_NAME_START -->{name}<!-- {key}_NAME_END --></text>'
        )
        parts.append(
            f'<rect x="{track_x}" y="{row_y}" width="{track_w}" height="12" '
            f'rx="2" fill="{L.TRACK}"/>'
        )
        parts.append(
            f'<rect id="{key.lower().replace("_", "-")}-bar" x="{track_x}" y="{row_y}" '
            f'width="{bar_w}" height="12" rx="2" fill="{bar_fill}"/>'
        )
        parts.append(
            f'<text x="{value_x}" y="{row_y + 10}" font-family="monospace" '
            f'font-size="11" fill="{L.TEXT_MUTED}" text-anchor="end">'
            f'<!-- {key}_VALUE_START -->{value}<!-- {key}_VALUE_END --></text>'
        )
    return "".join(parts)


def _enjoy_strip(enjoy: dict[str, Any]) -> str:
    """Render the WHAT I ENJOY strip panel + closing tagline.

    Header at top, four equal cards in a horizontal row, a dotted lime
    divider at the bottom, and the closing tagline centered under it.
    All inside the single ``ENJOY_PANEL`` rect.
    """
    parts: list[str] = []
    panel: L.Rect = L.ENJOY_PANEL
    inner_pad: int = 24
    parts.append(
        _section_header("WHAT I ENJOY", x=panel.x + inner_pad, y=panel.y + 32, icon="heart")
    )
    cards: list[dict[str, Any]] = enjoy.get("cards", [])
    if cards:
        inner_left: int = panel.x + inner_pad
        inner_w: int = panel.w - 2 * inner_pad
        card_gap: int = 16
        card_w: float = (inner_w - card_gap * (len(cards) - 1)) / len(cards)
        card_top: int = panel.y + 56
        for index, card in enumerate(cards):
            cx: float = inner_left + index * (card_w + card_gap)
            parts.append(
                embed_icon(UI_ICONS_DIR / f"{card['icon']}.svg", x=cx, y=card_top, size=22)
            )
            parts.append(
                _outlined_text(
                    card["title"],
                    INTER_BOLD,
                    size_px=15,
                    x=int(cx + 32),
                    y=card_top + 17,
                    fill=L.ACCENT,
                )
            )
            for line_index, line in enumerate(card.get("description", [])):
                line_y: int = card_top + 42 + line_index * 18
                parts.append(
                    f'<text x="{cx:g}" y="{line_y}" font-family="monospace" '
                    f'font-size="11" fill="{L.TEXT_MUTED}">{line}</text>'
                )

    dot_y: int = panel.bottom - 36
    dot_count: int = 60
    dot_x_start: int = panel.x + inner_pad
    dot_x_end: int = panel.right - inner_pad
    dot_spacing: float = (dot_x_end - dot_x_start) / max(dot_count - 1, 1)
    parts.extend(
        f'<circle cx="{round(dot_x_start + i * dot_spacing)}" cy="{dot_y}" r="1" fill="{L.ACCENT_DIM}"/>'
        for i in range(dot_count)
    )

    closing_y: int = panel.bottom - 14
    parts.append(
        f'<text x="{panel.cx}" y="{closing_y}" font-family="monospace" font-size="13" '
        f'fill="{L.TEXT_MUTED}" text-anchor="middle">'
        f'<tspan>Thanks for stopping by! Let’s </tspan>'
        f'<tspan fill="{L.ACCENT}">build the future</tspan>'
        f'<tspan> together.</tspan>'
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
    parts.append(_top_panel(about, system_info))
    parts.append(L.panel(L.TECH_PANEL))
    parts.append(_tech_strip(tech_stack))
    parts.append(L.panel(L.STATS_GLANCE))
    parts.append(_stats_glance())
    parts.append(L.panel(L.STATS_CONTRIB))
    parts.append(_stats_contrib())
    parts.append(L.panel(L.STATS_LANGS))
    parts.append(_stats_langs())
    parts.append(L.panel(L.ENJOY_PANEL))
    parts.append(_enjoy_strip(enjoy))

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
