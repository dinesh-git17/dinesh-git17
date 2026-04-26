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
import random
import sys
from pathlib import Path
from typing import Any

import yaml

from scripts.lib import dashboard_layout as dl
from scripts.lib import svg_animation as anim
from scripts.lib.svg_primitives import embed_icon
from scripts.lib.text_to_path import measure, outline

REPO_ROOT: Path = Path(__file__).resolve().parent.parent
CONTENT_DIR: Path = REPO_ROOT / "content"
ASSETS_DIR: Path = REPO_ROOT / "assets"
TECH_ICONS_DIR: Path = ASSETS_DIR / "icons" / "tech"
UI_ICONS_DIR: Path = ASSETS_DIR / "icons" / "ui"
_MIN_LEADER_PX: int = 16
PORTRAIT_PATH: Path = ASSETS_DIR / "portrait-card-2.png"
BRAIN_CARD_PATH: Path = ASSETS_DIR / "brain-ai-card.png"
OUTPUT_PATH: Path = ASSETS_DIR / "dashboard.svg"
INTER_BOLD: Path = REPO_ROOT / "scripts" / "fonts" / "Inter" / "Inter-Bold.otf"
INTER_MEDIUM: Path = REPO_ROOT / "scripts" / "fonts" / "Inter" / "Inter-Medium.otf"
INTER_REGULAR: Path = REPO_ROOT / "scripts" / "fonts" / "Inter" / "Inter-Regular.otf"


def _outlined_text(
    text: str, font: Path, size_px: int, x: int, y: int, fill: str
) -> str:
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
        parts.append(
            embed_icon(
                UI_ICONS_DIR / f"{icon}.svg",
                x=x,
                y=y - 13,
                size=15,
                stroke=dl.TEXT,
                fill=dl.TEXT,
            )
        )
        text_x = x + 22
    parts.append(
        _outlined_text(text, INTER_BOLD, size_px=13, x=text_x, y=y, fill=dl.TEXT)
    )
    return "".join(parts)


def _portrait_card() -> str:
    """Render the sidebar portrait card.

    Layout: name (outlined Inter Bold) and role line (lime mono) at the
    top of the card, then the portrait photo filling the remaining space.
    The photo image carries its own badge / headline / grid overlay.
    """
    parts: list[str] = []
    card: dl.Rect = dl.PORTRAIT_CARD
    name_x: int = card.x + 20
    name_y: int = card.y + 36
    name_size: int = 20
    parts.append(
        _outlined_text(
            "Dinesh Dawonauth",
            INTER_BOLD,
            size_px=name_size,
            x=name_x,
            y=name_y,
            fill=dl.TEXT,
        )
    )
    name_w: float = measure("Dinesh Dawonauth", INTER_BOLD, size_px=name_size)
    prompt_x: int = name_x + int(name_w) + 8
    parts.append(
        _outlined_text(
            ">_", INTER_BOLD, size_px=name_size, x=prompt_x, y=name_y, fill=dl.ACCENT
        )
    )
    role_y: int = name_y + 20
    parts.append(
        f'<text x="{name_x}" y="{role_y}" font-family="monospace" font-size="11">'
        f'<tspan fill="{dl.ACCENT}">AI Engineer</tspan>'
        f'<tspan fill="{dl.TEXT_MUTED}"> · Developer · Builder</tspan>'
        f"</text>"
    )

    photo_pad: int = 16
    photo_x: int = card.x + photo_pad
    photo_y: int = role_y + 16
    photo_w: int = card.w - 2 * photo_pad
    photo_h: int = card.bottom - photo_y - photo_pad

    if PORTRAIT_PATH.exists():
        b64: str = base64.b64encode(PORTRAIT_PATH.read_bytes()).decode("ascii")
        parts.append(
            f'<image x="{photo_x}" y="{photo_y}" width="{photo_w}" height="{photo_h}" '
            f'href="data:image/png;base64,{b64}" preserveAspectRatio="xMidYMid slice"/>'
        )
    else:
        parts.append(
            f'<rect x="{photo_x}" y="{photo_y}" width="{photo_w}" height="{photo_h}" '
            f'fill="{dl.SURFACE_2}" stroke="{dl.BORDER}"/>'
        )
    return "".join(parts)


def _quote_card() -> str:
    """Render the sidebar quote card.

    Layout: a filled olive double-quote glyph (Phosphor ``quotes-fill``)
    in the top-left, then three lines of monospace body text wrapped to
    fit the remaining width.
    """
    parts: list[str] = []
    card: dl.Rect = dl.QUOTE_CARD
    glyph_size: int = 28
    glyph_x: int = card.x + 16
    glyph_y: int = card.y + 16
    glyph_cx: int = glyph_x + glyph_size // 2
    glyph_cy: int = glyph_y + glyph_size // 2
    parts.append(
        f'<g transform="rotate(180 {glyph_cx} {glyph_cy})">'
        + embed_icon(
            UI_ICONS_DIR / "quote.svg",
            x=glyph_x,
            y=glyph_y,
            size=glyph_size,
        )
        + "</g>"
    )
    text_x: int = card.x + 56
    line_stride: int = 22
    line1_y: int = card.y + 38
    lines: tuple[tuple[tuple[str, str], ...], ...] = (
        ((dl.TEXT, "The most important use of a tool"),),
        ((dl.TEXT, "as powerful as "), (dl.ACCENT, "AI"), (dl.TEXT, " is to augment")),
        ((dl.TEXT, "humanity, not to replace it."),),
    )
    for index, segments in enumerate(lines):
        line_y: int = line1_y + index * line_stride
        spans: str = "".join(
            f'<tspan fill="{fill}">{text}</tspan>' for fill, text in segments
        )
        parts.append(
            f'<text x="{text_x}" y="{line_y}" font-family="monospace" '
            f'font-size="12">{spans}</text>'
        )
    return "".join(parts)


def _connect_card(connect: dict[str, Any]) -> str:
    """Render the sidebar connect card with rows of icon + label.

    Header is a quiet muted-grey label (no leading icon) sitting above
    four icon+label rows in white. Brand glyphs (linkedin, discord) and
    Lucide outlines (mail, globe) are recoloured to ``dl.TEXT`` via
    ``embed_icon`` overrides so the row reads as a single typographic unit.
    """
    parts: list[str] = []
    card: dl.Rect = dl.CONNECT_CARD
    header_x: int = card.x + 20
    header_y: int = card.y + 32
    parts.append(
        f'<text x="{header_x}" y="{header_y}" font-family="monospace" '
        f'font-size="12" font-weight="bold" letter-spacing="2" '
        f'fill="{dl.TEXT_MUTED}">CONNECT</text>'
    )
    rows: list[dict[str, str]] = connect.get("rows", [])
    row_origin_y: int = card.y + 70
    row_stride: int = 32
    icon_size: int = 18
    for index, row in enumerate(rows):
        row_y: int = row_origin_y + index * row_stride
        icon_path: Path = UI_ICONS_DIR / f"{row['icon']}.svg"
        parts.append(
            embed_icon(
                icon_path,
                x=header_x,
                y=row_y - 14,
                size=icon_size,
                stroke=dl.TEXT,
                fill=dl.TEXT,
            )
        )
        parts.append(
            f'<text x="{header_x + 30}" y="{row_y}" font-family="monospace" '
            f'font-size="13" fill="{dl.TEXT}">{row["label"]}</text>'
        )
    return "".join(parts)


def _cta_card() -> str:
    """Render the sidebar CTA card with a green-prompted build line.

    Layout: a lime ``>`` prompt followed by ``Let's build something`` on
    line one, and ``meaningful together.`` (with ``meaningful`` in lime)
    on line two. A sparse three-row "data rain" of dim-lime dots fills
    the bottom of the card. No header, no trailing collaborations line.
    """
    parts: list[str] = []
    card: dl.Rect = dl.CTA_CARD
    prompt_x: int = card.x + 22
    text_x: int = prompt_x + 22
    line1_y: int = card.y + 56
    line2_y: int = line1_y + 28
    body_size: int = 16

    parts.append(
        f'<text x="{prompt_x}" y="{line1_y}" font-family="monospace" '
        f'font-size="{body_size}" font-weight="bold" '
        f'fill="{dl.ACCENT}">&gt;</text>'
    )
    parts.append(
        f'<text x="{text_x}" y="{line1_y}" font-family="monospace" '
        f'font-size="{body_size}" fill="{dl.TEXT}">'
        f"Let's build something</text>"
    )
    parts.append(
        f'<text x="{text_x}" y="{line2_y}" font-family="monospace" '
        f'font-size="{body_size}">'
        f'<tspan fill="{dl.ACCENT}">meaningful</tspan>'
        f'<tspan fill="{dl.TEXT}"> together.</tspan>'
        f"</text>"
    )

    rain_x_start: int = card.x + 16
    rain_x_end: int = card.right - 16
    rain_bottom_y: int = card.bottom - 14
    rng: random.Random = random.Random(0xC7A0)  # noqa: S311 (visual jitter, not security)
    densities: tuple[float, ...] = (0.70, 0.50, 0.34, 0.20, 0.10)
    for row_index, density in enumerate(densities):
        row_y: int = rain_bottom_y - row_index * 7
        parts.extend(
            f'<circle cx="{px}" cy="{row_y}" r="1" fill="{dl.ACCENT_DIM}"/>'
            for px in range(rain_x_start, rain_x_end, 4)
            if rng.random() < density
        )
    return "".join(parts)


_CANADA_RED_PATH: str = (
    "m0 0h2400l99 99h4602l99-99h2400v4800h-2400l-99-99h-4602l-99 99H0z"
)
_CANADA_WHITE_PATH: str = (
    "m2400 0h4800v4800h-4800zm2490 4430-45-863a95 95 0 0 1 111-98l859 151"
    "-116-320a65 65 0 0 1 20-73l941-762-212-99a65 65 0 0 1-34-79l186-572"
    "-542 115a65 65 0 0 1-73-38l-105-247-423 454a65 65 0 0 1-111-57l204-1052"
    "-327 189a65 65 0 0 1-91-27l-332-652-332 652a65 65 0 0 1-91 27l-327-189"
    " 204 1052a65 65 0 0 1-111 57l-423-454-105 247a65 65 0 0 1-73 38l-542-115"
    " 186 572a65 65 0 0 1-34 79l-212 99 941 762a65 65 0 0 1 20 73l-116 320"
    " 859-151a95 95 0 0 1 111 98l-45 863z"
)


def _canada_flag(x: int, y: int, width: int, height: int) -> str:
    """Render the Canadian flag with maple leaf.

    Source paths: Wikimedia Commons "Flag of Canada" SVG (viewBox 9600x4800).
    The white path's leaf subpath uses opposite winding so the default
    nonzero fill rule cuts a hole, exposing the red underneath.
    """
    sx: float = width / 9600
    sy: float = height / 4800
    return (
        f'<g transform="translate({x},{y}) scale({sx},{sy})">'
        f'<path fill="#D52B1E" d="{_CANADA_RED_PATH}"/>'
        f'<path fill="#FFFFFF" d="{_CANADA_WHITE_PATH}"/>'
        f"</g>"
    )


def _top_panel(about: dict[str, Any], system_info: dict[str, Any]) -> str:  # noqa: PLR0915 (layout-driven; splits would fragment one cohesive panel)
    """Render the top panel: ABOUT ME on the left, SYSTEM INFO on the right.

    Mirrors the mockup pixel by pixel: large user icon header, sans-serif
    body prose, a single row of four compact trait pills with proportional
    Inter Regular labels, and SYSTEM INFO rows with bold Inter labels in
    olive plus dotted leaders to monospace right-aligned values.
    """
    parts: list[str] = []
    panel: dl.Rect = dl.TOP_PANEL
    inner_pad: int = 28
    divider_x: int = panel.cx
    parts.append(
        f'<line x1="{divider_x}" y1="{panel.y + inner_pad}" '
        f'x2="{divider_x}" y2="{panel.bottom - inner_pad}" '
        f'stroke="{dl.BORDER}"/>'
    )

    about_x: int = panel.x + inner_pad
    header_icon_size: int = 26
    header_icon_y: int = panel.y + 38
    header_text_x: int = about_x + header_icon_size + 16
    parts.append(
        embed_icon(
            UI_ICONS_DIR / "user.svg",
            x=about_x,
            y=header_icon_y,
            size=header_icon_size,
        )
    )
    parts.append(
        _outlined_text(
            "ABOUT ME",
            INTER_BOLD,
            size_px=15,
            x=header_text_x,
            y=header_icon_y + 19,
            fill=dl.TEXT,
        )
    )

    if BRAIN_CARD_PATH.exists():
        brain_size: int = 130
        brain_x: int = divider_x - inner_pad - brain_size
        brain_y: int = panel.y + 80
        b64: str = base64.b64encode(BRAIN_CARD_PATH.read_bytes()).decode("ascii")
        parts.append(
            f'<image x="{brain_x}" y="{brain_y}" width="{brain_size}" '
            f'height="{brain_size}" opacity="0.3" '
            f'href="data:image/png;base64,{b64}"/>'
        )

    bio_lines: list[str] = about.get("bio", [])
    bio_origin_y: int = panel.y + 110
    bio_line_h: int = 26
    bio_size_px: int = 15
    for index, line in enumerate(bio_lines):
        line_y: int = bio_origin_y + index * bio_line_h
        parts.append(
            _outlined_text(
                line,
                INTER_REGULAR,
                size_px=bio_size_px,
                x=about_x,
                y=line_y,
                fill=dl.TEXT,
            )
        )

    pills: list[dict[str, str]] = about.get("trait_pills", [])
    if pills:
        pill_h: int = 36
        pill_gap_x: int = 8
        pill_inner_left: int = 10
        pill_icon_text_gap: int = 6
        pill_icon_size: int = 12
        pill_text_size: int = 10
        about_inner_w: int = divider_x - about_x - inner_pad
        pill_w: int = (about_inner_w - pill_gap_x * (len(pills) - 1)) // len(pills)
        pill_origin_y: int = panel.bottom - inner_pad - pill_h
        for index, pill in enumerate(pills):
            px: int = about_x + index * (pill_w + pill_gap_x)
            parts.append(
                f'<rect x="{px}" y="{pill_origin_y}" '
                f'width="{pill_w}" height="{pill_h}" '
                f'rx="8" fill="none" stroke="{dl.BORDER}"/>'
            )
            parts.append(
                embed_icon(
                    UI_ICONS_DIR / f"{pill['icon']}.svg",
                    x=px + pill_inner_left,
                    y=pill_origin_y + (pill_h - pill_icon_size) // 2,
                    size=pill_icon_size,
                )
            )
            text_x: int = px + pill_inner_left + pill_icon_size + pill_icon_text_gap
            text_baseline_y: int = pill_origin_y + pill_h // 2 + pill_text_size // 2 - 1
            parts.append(
                _outlined_text(
                    pill["label"],
                    INTER_REGULAR,
                    size_px=pill_text_size,
                    x=text_x,
                    y=text_baseline_y,
                    fill=dl.TEXT,
                )
            )

    sys_x: int = divider_x + inner_pad
    rows: list[dict[str, str]] = system_info.get("rows", [])
    icon_size: int = 22
    icon_label_gap: int = 16
    label_x: int = sys_x + icon_size + icon_label_gap
    value_right_x: int = panel.right - inner_pad
    leader_pad: int = 14
    label_size_px: int = 14
    rows_count: int = max(len(rows), 1)
    available_h: int = panel.h - 2 * inner_pad
    row_stride: int = available_h // rows_count
    row_origin_y: int = panel.y + inner_pad + row_stride // 2 + label_size_px // 2
    for index, row in enumerate(rows):
        row_y: int = row_origin_y + index * row_stride
        icon_path: Path = UI_ICONS_DIR / f"{row['icon']}.svg"
        parts.append(
            embed_icon(
                icon_path,
                x=sys_x,
                y=row_y - icon_size + 4,
                size=icon_size,
                stroke=dl.TEXT,
            )
        )
        parts.append(
            _outlined_text(
                row["label"],
                INTER_BOLD,
                size_px=label_size_px,
                x=label_x,
                y=row_y,
                fill=dl.ACCENT,
            )
        )
        if row.get("flag") == "CA":
            parts.append(
                _canada_flag(x=value_right_x - 22, y=row_y - 10, width=22, height=11)
            )
            value_anchor_x: int = value_right_x - 30
        else:
            value_anchor_x = value_right_x
        parts.append(
            f'<text x="{value_anchor_x}" y="{row_y}" font-family="monospace" '
            f'font-size="13" fill="{dl.TEXT}" text-anchor="end">{row["value"]}</text>'
        )
        label_w: float = measure(row["label"], INTER_BOLD, size_px=label_size_px)
        leader_start: int = label_x + int(label_w) + leader_pad
        leader_end: int = value_anchor_x - leader_pad
        if leader_end - leader_start > _MIN_LEADER_PX:
            parts.append(
                f'<line x1="{leader_start}" y1="{row_y - 5}" '
                f'x2="{leader_end}" y2="{row_y - 5}" '
                f'stroke="{dl.TEXT_MUTED}" stroke-width="1.2" stroke-opacity="0.55" '
                f'stroke-dasharray="0.1 6" stroke-linecap="round"/>'
            )
    return "".join(parts)


def _tech_strip(tech_stack: dict[str, Any]) -> str:
    """Render the TECH I WORK WITH strip panel.

    Compact header at the top of the panel followed by a single
    horizontal row of brand icons with a small label under each. Each
    column is separated from its neighbours by a thin vertical divider
    spanning the icon-and-label band.
    """
    parts: list[str] = []
    panel: dl.Rect = dl.TECH_PANEL
    inner_pad: int = 24
    parts.append(
        _section_header(
            "TECH I WORK WITH",
            x=panel.x + inner_pad,
            y=panel.y + 30,
            icon="square-terminal",
        )
    )
    icons: list[dict[str, str]] = tech_stack.get("icons", [])
    if not icons:
        return "".join(parts)
    icon_size: int = 36
    icons_top: int = panel.y + 52
    label_y: int = panel.bottom - 14
    inner_left: int = panel.x + inner_pad
    inner_w: int = panel.w - 2 * inner_pad
    column_w: float = inner_w / len(icons)

    divider_top: int = icons_top - 4
    divider_bottom: int = label_y + 4
    for index in range(1, len(icons)):
        divider_x: float = inner_left + index * column_w
        parts.append(
            f'<line x1="{divider_x:g}" y1="{divider_top}" '
            f'x2="{divider_x:g}" y2="{divider_bottom}" '
            f'stroke="{dl.BORDER}"/>'
        )

    for index, icon_info in enumerate(icons):
        slot_cx: float = inner_left + (index + 0.5) * column_w
        icon_x: float = slot_cx - icon_size / 2
        icon_path: Path = TECH_ICONS_DIR / icon_info["file"]
        parts.append(embed_icon(icon_path, x=icon_x, y=icons_top, size=icon_size))
        parts.append(
            f'<text x="{slot_cx:g}" y="{label_y}" font-family="monospace" '
            f'font-size="11" fill="{dl.TEXT}" text-anchor="middle">'
            f"{icon_info['label']}</text>"
        )
    return "".join(parts)


_GLANCE_ROWS: tuple[tuple[str, str, str], ...] = (
    ("Total Stars Earned", "STARS", "116"),
    ("Total Commits (last year)", "COMMITS", "3.8k"),
    ("Total PRs", "PRS", "818"),
    ("Total Issues", "ISSUES", "36"),
    ("Contributed to (last year)", "CONTRIB_TO", "3"),
)

_LANG_ROWS: tuple[tuple[str, str, str, int, str], ...] = (
    ("LANG_1", "Python", "30 hrs", 180, dl.ACCENT),
    ("LANG_2", "TypeScript", "5 hrs 12 mins", 31, dl.ACCENT_DIM),
    ("LANG_3", "JavaScript", "3 hrs 9 mins", 19, dl.ACCENT_DIM),
    ("LANG_4", "Bash", "1 hr 24 mins", 8, dl.ACCENT_DIM),
    ("LANG_5", "Rust", "45 mins", 5, dl.ACCENT_DIM),
)


def _stats_glance() -> str:
    """Render the GITHUB AT A GLANCE card with 5 metric rows + grade ring."""
    parts: list[str] = []
    card: dl.Rect = dl.STATS_GLANCE
    parts.append(
        _section_header(
            "GITHUB AT A GLANCE", x=card.x + 20, y=card.y + 32, icon="github"
        )
    )
    label_x: int = card.x + 20
    value_x: int = card.x + 235
    row_origin_y: int = card.y + 72
    row_stride: int = 32
    for index, (label, key, value) in enumerate(_GLANCE_ROWS):
        row_y: int = row_origin_y + index * row_stride
        begin_s: float = anim.BOOT_STATS_BEGIN_S + index * anim.BOOT_STATS_STAGGER_S
        row_anim: str = anim.boot_animate(
            attribute="opacity",
            from_value="0",
            to_value="1",
            begin_s=begin_s,
            dur_s=anim.BOOT_STATS_DUR_S,
        )
        parts.append(f'<g opacity="1">{row_anim}')
        parts.append(
            f'<text x="{label_x}" y="{row_y}" font-family="monospace" '
            f'font-size="12" fill="{dl.TEXT}">{label}</text>'
        )
        parts.append(
            f'<text x="{value_x}" y="{row_y}" font-family="monospace" '
            f'font-size="12" fill="{dl.TEXT}" text-anchor="end">'
            f"<!-- {key}_START -->{value}<!-- {key}_END --></text>"
        )
        parts.append("</g>")

    ring_cx: int = card.right - 60
    ring_cy: int = card.y + 132
    ring_r: int = 38
    ring_circumference: int = round(2 * 3.14159 * ring_r)
    arc_len: int = round(ring_circumference * 0.75)
    parts.append(
        f'<circle cx="{ring_cx}" cy="{ring_cy}" r="{ring_r}" fill="none" '
        f'stroke="{dl.TRACK}" stroke-width="6"/>'
    )
    ring_anim: str = anim.boot_animate(
        attribute="stroke-dashoffset",
        from_value=str(ring_circumference),
        to_value="0",
        begin_s=anim.BOOT_STATS_BEGIN_S,
        dur_s=anim.BOOT_RING_DUR_S,
    )
    parts.append(
        f'<circle id="grade-ring" cx="{ring_cx}" cy="{ring_cy}" '
        f'r="{ring_r}" fill="none" stroke="{dl.ACCENT}" stroke-width="6" '
        f'stroke-dasharray="{arc_len} {ring_circumference}" '
        f'stroke-dashoffset="0" transform="rotate(-90 {ring_cx} {ring_cy})" '
        f'stroke-linecap="round">{ring_anim}</circle>'
    )
    letter_anim: str = anim.boot_animate(
        attribute="opacity",
        from_value="0",
        to_value="1",
        begin_s=anim.BOOT_STATS_BEGIN_S + 0.2,
        dur_s=anim.BOOT_NUMBER_DUR_S,
    )
    parts.append(
        f'<g opacity="1">{letter_anim}'
        f'<text x="{ring_cx}" y="{ring_cy + 8}" font-family="monospace" font-size="22" '
        f'font-weight="bold" fill="{dl.TEXT}" text-anchor="middle">'
        f"<!-- GRADE_LETTER_START -->A<!-- GRADE_LETTER_END --></text>"
        f"</g>"
    )
    parts.append(
        f'<text x="{ring_cx}" y="{ring_cy + ring_r + 30}" '
        f'font-family="monospace" font-size="11" '
        f'fill="{dl.TEXT_MUTED}" text-anchor="middle">Overall Grade</text>'
    )
    return "".join(parts)


def _stats_contrib() -> str:
    """Render the CONTRIBUTION OVERVIEW card: total + current + longest streak."""
    parts: list[str] = []
    card: dl.Rect = dl.STATS_CONTRIB
    parts.append(
        _section_header(
            "CONTRIBUTION OVERVIEW", x=card.x + 20, y=card.y + 32, icon="calendar"
        )
    )
    col_w: int = card.w // 3
    col_centres: list[int] = [card.x + col_w // 2 + i * col_w for i in range(3)]

    divider_top: int = card.y + 65
    divider_bottom: int = card.y + 215
    for i in range(1, 3):
        divider_x: int = card.x + i * col_w
        parts.append(
            f'<line x1="{divider_x}" y1="{divider_top}" '
            f'x2="{divider_x}" y2="{divider_bottom}" '
            f'stroke="{dl.BORDER}" stroke-width="1"/>'
        )

    number_y: int = card.y + 132
    label_y: int = card.y + 168
    date_y: int = card.y + 186

    total_cx: int = col_centres[0]
    parts.append(
        f'<text x="{total_cx}" y="{number_y}" font-family="monospace" font-size="30" '
        f'font-weight="bold" fill="{dl.TEXT}" text-anchor="middle">'
        f"<!-- TOTAL_CONTRIB_START -->5,981<!-- TOTAL_CONTRIB_END --></text>"
    )
    parts.append(
        f'<text x="{total_cx}" y="{label_y}" font-family="monospace" font-size="9" '
        f'fill="{dl.TEXT_MUTED}" text-anchor="middle">Total Contributions</text>'
    )
    parts.append(
        f'<text x="{total_cx}" y="{date_y}" font-family="monospace" font-size="8" '
        f'fill="{dl.TEXT_MUTED}" text-anchor="middle">'
        f"<!-- TOTAL_CONTRIB_RANGE_START -->"
        f"Jan 1, 2025 - Present"
        f"<!-- TOTAL_CONTRIB_RANGE_END --></text>"
    )

    streak_cx: int = col_centres[1]
    streak_cy: int = number_y - 12
    streak_r: int = 46
    streak_circumference: int = round(2 * 3.14159 * streak_r)
    parts.append(
        f'<circle cx="{streak_cx}" cy="{streak_cy}" r="{streak_r}" fill="none" '
        f'stroke="{dl.TRACK}" stroke-width="6"/>'
    )
    parts.append(
        f'<circle id="streak-ring" cx="{streak_cx}" cy="{streak_cy}" '
        f'r="{streak_r}" fill="none" stroke="{dl.ACCENT}" stroke-width="6" '
        f'stroke-dasharray="{streak_circumference} {streak_circumference}" '
        f'stroke-dashoffset="0" transform="rotate(-90 {streak_cx} {streak_cy})" '
        f'stroke-linecap="round"/>'
    )
    parts.append(
        f'<text x="{streak_cx}" y="{streak_cy + 11}" '
        f'font-family="monospace" font-size="30" font-weight="bold" '
        f'fill="{dl.TEXT}" text-anchor="middle">'
        f"<!-- CURRENT_STREAK_START -->85<!-- CURRENT_STREAK_END --></text>"
    )
    parts.append(
        f'<text x="{streak_cx}" y="{streak_cy + streak_r + 28}" '
        f'font-family="monospace" font-size="9" '
        f'fill="{dl.TEXT_MUTED}" text-anchor="middle">Current Streak</text>'
    )
    parts.append(
        f'<text x="{streak_cx}" y="{streak_cy + streak_r + 46}" '
        f'font-family="monospace" font-size="8" '
        f'fill="{dl.TEXT_MUTED}" text-anchor="middle">'
        f"<!-- CURRENT_STREAK_RANGE_START -->"
        f"Jan 31 - Apr 25"
        f"<!-- CURRENT_STREAK_RANGE_END --></text>"
    )

    longest_cx: int = col_centres[2]
    parts.append(
        f'<text x="{longest_cx}" y="{number_y}" font-family="monospace" font-size="30" '
        f'font-weight="bold" fill="{dl.TEXT}" text-anchor="middle">'
        f"<!-- LONGEST_STREAK_START -->85<!-- LONGEST_STREAK_END --></text>"
    )
    parts.append(
        f'<text x="{longest_cx}" y="{label_y}" font-family="monospace" font-size="9" '
        f'fill="{dl.TEXT_MUTED}" text-anchor="middle">Longest Streak</text>'
    )
    parts.append(
        f'<text x="{longest_cx}" y="{date_y}" font-family="monospace" font-size="8" '
        f'fill="{dl.TEXT_MUTED}" text-anchor="middle">'
        f"<!-- LONGEST_STREAK_RANGE_START -->"
        f"Jan 31 - Apr 25"
        f"<!-- LONGEST_STREAK_RANGE_END --></text>"
    )
    return "".join(parts)


def _stats_langs() -> str:
    """Render the TOP LANGUAGES (BY HOURS) card with 5 bar rows + tracks."""
    parts: list[str] = []
    card: dl.Rect = dl.STATS_LANGS
    header_x: int = card.x + 20
    header_y: int = card.y + 32
    parts.append(
        embed_icon(
            UI_ICONS_DIR / "code-xml.svg",
            x=header_x,
            y=header_y - 13,
            size=15,
            stroke=dl.ACCENT,
        )
    )
    parts.append(
        _outlined_text(
            "TOP LANGUAGES",
            INTER_BOLD,
            size_px=13,
            x=header_x + 22,
            y=header_y,
            fill=dl.TEXT,
        )
    )
    title_w: float = measure("TOP LANGUAGES", INTER_BOLD, size_px=13)
    suffix_x: float = header_x + 22 + title_w + 8
    parts.append(
        f'<text x="{suffix_x:g}" y="{header_y}" font-family="monospace" '
        f'font-size="10" fill="{dl.TEXT_MUTED}">(BY HOURS)</text>'
    )
    parts.append(
        "<defs>"
        f'<linearGradient id="bar-fade-accent" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{dl.ACCENT}" stop-opacity="1"/>'
        f'<stop offset="0.78" stop-color="{dl.ACCENT}" stop-opacity="1"/>'
        f'<stop offset="1" stop-color="{dl.ACCENT}" stop-opacity="0"/>'
        f"</linearGradient>"
        f'<linearGradient id="bar-fade-accent-dim" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{dl.ACCENT_DIM}" stop-opacity="1"/>'
        f'<stop offset="0.78" stop-color="{dl.ACCENT_DIM}" stop-opacity="1"/>'
        f'<stop offset="1" stop-color="{dl.ACCENT_DIM}" stop-opacity="0"/>'
        f"</linearGradient>"
        "</defs>"
    )
    label_x: int = card.x + 20
    track_x: int = card.x + 100
    track_w: int = 145
    value_x: int = card.right - 18
    row_origin_y: int = card.y + 76
    row_stride: int = 34
    bar_height: int = 10
    bar_radius: int = 5
    legacy_max: int = 184
    for index, (key, name, value, bar_w, bar_fill) in enumerate(_LANG_ROWS):
        row_y: int = row_origin_y + index * row_stride
        scaled_bar_w: int = max(2, round(bar_w * track_w / legacy_max))
        gradient_id: str = (
            "bar-fade-accent" if bar_fill == dl.ACCENT else "bar-fade-accent-dim"
        )
        parts.append(
            f'<text x="{label_x}" y="{row_y + 9}" font-family="monospace" '
            f'font-size="12" fill="{dl.TEXT}">'
            f"<!-- {key}_NAME_START -->{name}<!-- {key}_NAME_END --></text>"
        )
        parts.append(
            f'<rect x="{track_x}" y="{row_y}" width="{track_w}" height="{bar_height}" '
            f'rx="{bar_radius}" fill="{dl.TRACK}"/>'
        )
        bar_id: str = f"{key.lower().replace('_', '-')}-bar"
        parts.append(
            f'<rect id="{bar_id}" x="{track_x}" y="{row_y}" '
            f'width="{scaled_bar_w}" height="{bar_height}" '
            f'rx="{bar_radius}" fill="url(#{gradient_id})"/>'
        )
        parts.append(
            f'<text x="{value_x}" y="{row_y + 9}" font-family="monospace" '
            f'font-size="11" fill="{dl.TEXT_MUTED}" text-anchor="end">'
            f"<!-- {key}_VALUE_START -->{value}<!-- {key}_VALUE_END --></text>"
        )
    return "".join(parts)


def _enjoy_strip(enjoy: dict[str, Any]) -> str:
    """Render the WHAT I ENJOY strip panel + closing tagline.

    Header at top, four equal cards in a horizontal row, a dotted lime
    divider at the bottom, and the closing tagline centered under it.
    All inside the single ``ENJOY_PANEL`` rect.
    """
    parts: list[str] = []
    panel: dl.Rect = dl.ENJOY_PANEL
    inner_pad: int = 24
    header_x: int = panel.x + inner_pad
    header_y: int = panel.y + 32
    parts.append(
        embed_icon(
            UI_ICONS_DIR / "heart.svg",
            x=header_x,
            y=header_y - 13,
            size=15,
            stroke=dl.ACCENT,
        )
    )
    parts.append(
        _outlined_text(
            "WHAT I ENJOY",
            INTER_BOLD,
            size_px=13,
            x=header_x + 22,
            y=header_y,
            fill=dl.TEXT,
        )
    )
    cards: list[dict[str, Any]] = enjoy.get("cards", [])
    card_top: int = panel.y + 60
    card_bottom: int = panel.y + 132
    if cards:
        inner_left: int = panel.x + inner_pad
        inner_w: int = panel.w - 2 * inner_pad
        card_gap: int = 16
        card_w: float = (inner_w - card_gap * (len(cards) - 1)) / len(cards)
        icon_size: int = 44
        for i in range(1, len(cards)):
            divider_x: float = inner_left + i * (card_w + card_gap) - card_gap / 2
            parts.append(
                f'<line x1="{divider_x:g}" y1="{card_top - 4}" '
                f'x2="{divider_x:g}" y2="{card_bottom + 4}" '
                f'stroke="{dl.BORDER}" stroke-width="1"/>'
            )
        for index, card in enumerate(cards):
            cx: float = inner_left + index * (card_w + card_gap)
            text_x: float = cx + icon_size + 14
            parts.append(
                embed_icon(
                    UI_ICONS_DIR / f"{card['icon']}.svg",
                    x=cx,
                    y=card_top + 6,
                    size=icon_size,
                    stroke=dl.ACCENT,
                )
            )
            parts.append(
                _outlined_text(
                    card["title"],
                    INTER_BOLD,
                    size_px=15,
                    x=int(text_x),
                    y=card_top + 24,
                    fill=dl.ACCENT,
                )
            )
            for line_index, line in enumerate(card.get("description", [])):
                line_y: int = card_top + 46 + line_index * 16
                parts.append(
                    f'<text x="{text_x:g}" y="{line_y}" font-family="monospace" '
                    f'font-size="10" fill="{dl.TEXT_MUTED}">{line}</text>'
                )

    rng: random.Random = random.Random(0xE301)  # noqa: S311 (visual jitter, not security)
    rain_left: int = panel.x + inner_pad
    rain_right: int = panel.right - inner_pad
    rain_w: int = rain_right - rain_left
    rain_rows: int = 5
    rain_top: int = panel.y + 138
    row_stride: int = 6
    densities: tuple[float, ...] = (0.08, 0.16, 0.28, 0.44, 0.62)
    for row_i in range(rain_rows):
        row_y: int = rain_top + row_i * row_stride
        density: float = densities[row_i]
        parts.extend(
            f'<circle cx="{rain_left + x_i}" cy="{row_y}" '
            f'r="1" fill="{dl.ACCENT_DIM}"/>'
            for x_i in range(0, rain_w, 4)
            if rng.random() < density
        )

    closing_y: int = panel.bottom - 8
    parts.append(
        f'<text x="{panel.cx}" y="{closing_y}" font-family="monospace" font-size="13" '
        f'fill="{dl.TEXT_MUTED}" text-anchor="middle">'
        f"<tspan>Thanks for stopping by! Let's </tspan>"
        f'<tspan fill="{dl.ACCENT}">build the future</tspan>'
        f"<tspan> together.</tspan>"
        f"</text>"
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
    parts.append(dl.svg_open())
    parts.append(dl.canvas_background())
    parts.append(dl.outer_frame())

    parts.append(dl.panel(dl.PORTRAIT_CARD))
    parts.append(_portrait_card())
    parts.append(dl.panel(dl.QUOTE_CARD))
    parts.append(_quote_card())
    parts.append(dl.panel(dl.CONNECT_CARD))
    parts.append(_connect_card(connect))
    parts.append(dl.panel(dl.CTA_CARD))
    parts.append(_cta_card())

    parts.append(dl.panel(dl.TOP_PANEL))
    parts.append(_top_panel(about, system_info))
    parts.append(dl.panel(dl.TECH_PANEL))
    parts.append(_tech_strip(tech_stack))
    parts.append(dl.panel(dl.STATS_GLANCE))
    parts.append(_stats_glance())
    parts.append(dl.panel(dl.STATS_CONTRIB))
    parts.append(_stats_contrib())
    parts.append(dl.panel(dl.STATS_LANGS))
    parts.append(_stats_langs())
    parts.append(dl.panel(dl.ENJOY_PANEL))
    parts.append(_enjoy_strip(enjoy))

    parts.append("</svg>")
    return "".join(parts)


def _read_yaml(path: Path) -> dict[str, Any]:
    """Read and parse a YAML file."""
    parsed: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8"))
    return parsed


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
