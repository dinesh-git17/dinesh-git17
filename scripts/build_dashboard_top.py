"""Build the static top-zone SVG for the GitHub profile dashboard.

Reads content from ``content/*.yml``, composes the SVG layout (hero strip,
portrait card, ABOUT ME panel, system info column, tech stack strip, quote
block, CONNECT block, CTA line), embeds the portrait PNG and tech/UI icons,
outlines display text via :mod:`scripts.lib.text_to_path`, and writes the
result to ``assets/dashboard-top.svg``.

Run manually when content YAMLs change. Not part of the daily Action.
"""

import base64
import re
import sys
from pathlib import Path
from typing import Any

import yaml

from scripts.lib.text_to_path import outline

REPO_ROOT: Path = Path(__file__).resolve().parent.parent
CONTENT_DIR: Path = REPO_ROOT / "content"
ASSETS_DIR: Path = REPO_ROOT / "assets"
TECH_ICONS_DIR: Path = ASSETS_DIR / "icons" / "tech"
UI_ICONS_DIR: Path = ASSETS_DIR / "icons" / "ui"
PORTRAIT_PATH: Path = ASSETS_DIR / "portrait-card.png"
OUTPUT_PATH: Path = ASSETS_DIR / "dashboard-top.svg"
INTER_BOLD: Path = REPO_ROOT / "scripts" / "fonts" / "Inter" / "Inter-Bold.otf"
INTER_MEDIUM: Path = REPO_ROOT / "scripts" / "fonts" / "Inter" / "Inter-Medium.otf"

ACCENT: str = "#9EFF5A"
TEXT: str = "#E8E8E0"
TEXT_MUTED: str = "#8B92A5"
BG: str = "#0A0E1A"
SURFACE: str = "#11151F"
BORDER: str = "#1F2533"


_INHERITABLE_ICON_ATTRS: tuple[str, ...] = (
    "fill",
    "stroke",
    "stroke-width",
    "stroke-linecap",
    "stroke-linejoin",
)


def embed_icon(icon_path: Path, x: int, y: int, size: int) -> str:
    """Return a ``<g>`` element that embeds an icon's inner SVG content.

    The icon file's outer ``<svg>`` element is stripped; only its child
    elements are inlined inside a translate+scale group positioned at
    (``x``, ``y``) with a uniform scale chosen so the icon's source viewBox
    maps to ``size`` pixels. Presentation attributes that Lucide-style
    outline icons set on the root ``<svg>`` (``fill``, ``stroke``,
    ``stroke-width``, ``stroke-linecap``, ``stroke-linejoin``) are
    forwarded onto the wrapping ``<g>`` so the children inherit them.

    Args:
        icon_path: Path to the source SVG icon.
        x: Target x position (top-left of the icon in the parent SVG).
        y: Target y position.
        size: Target rendered size in pixels (square).

    Returns:
        An SVG ``<g>`` element string.

    Raises:
        FileNotFoundError: If ``icon_path`` does not exist.
        ValueError: If the icon does not contain a ``viewBox`` attribute.
    """
    content: str = icon_path.read_text(encoding="utf-8")
    viewbox_match: re.Match[str] | None = re.search(
        r'viewBox\s*=\s*"([^"]+)"', content
    )
    if viewbox_match is None:
        msg = f"icon {icon_path.name} has no viewBox"
        raise ValueError(msg)
    parts: list[str] = viewbox_match.group(1).split()
    source_size: float = max(float(parts[2]), float(parts[3]))
    scale: float = size / source_size

    root_match: re.Match[str] | None = re.match(r"<svg\b[^>]*>", content, re.DOTALL)
    if root_match is None:
        msg = f"icon {icon_path.name} has no <svg> root"
        raise ValueError(msg)
    inherited: list[str] = []
    for attr in _INHERITABLE_ICON_ATTRS:
        attr_match: re.Match[str] | None = re.search(
            rf'\s{re.escape(attr)}="([^"]*)"', root_match.group(0)
        )
        if attr_match is not None:
            inherited.append(f'{attr}="{attr_match.group(1)}"')

    inner_match: re.Match[str] | None = re.search(
        r"<svg[^>]*>(.*)</svg>", content, re.DOTALL
    )
    if inner_match is None:
        msg = f"icon {icon_path.name} has no closing </svg>"
        raise ValueError(msg)
    inner: str = inner_match.group(1).strip()

    inherited_attrs: str = (" " + " ".join(inherited)) if inherited else ""
    return (
        f'<g transform="translate({x},{y}) scale({scale:.4f})"'
        f'{inherited_attrs}>{inner}</g>'
    )


def label_value_row(
    icon_path: Path,
    x: int,
    y: int,
    label: str,
    value: str,
    label_x_offset: int = 32,
    value_x_offset: int = 140,
) -> str:
    """Render a single icon + lime label + mono value row.

    Used in the system info column. Icon is at (x, y); label is positioned
    at ``x + label_x_offset``; value is positioned at ``x + value_x_offset``.

    Args:
        icon_path: Path to the lime UI icon SVG.
        x: Row's left x coordinate.
        y: Row's baseline y coordinate.
        label: Lime-coloured key text.
        value: Mono-coloured value text. May contain XML comment markers.
        label_x_offset: Label's x relative to ``x``.
        value_x_offset: Value's x relative to ``x``.

    Returns:
        An SVG fragment (multiple elements, no wrapper).
    """
    icon_y: int = y - 14
    icon_g: str = embed_icon(icon_path, x=x, y=icon_y, size=18)
    return (
        f"{icon_g}"
        f'<text x="{x + label_x_offset}" y="{y}" '
        f'font-family="monospace" font-size="13" fill="{ACCENT}">{label}</text>'
        f'<text x="{x + value_x_offset}" y="{y}" '
        f'font-family="monospace" font-size="13" fill="{TEXT}">{value}</text>'
    )


def canada_flag(x: int, y: int, width: int, height: int) -> str:
    """Render a small inline Canadian flag using three coloured rects.

    The flag is a simplified red-white-red banner — the maple leaf is
    omitted at this scale because it would not render legibly inside an
    SVG patched without ``<defs>`` or ``<image>``.

    Args:
        x: Top-left x coordinate.
        y: Top-left y coordinate.
        width: Total flag width (sum of three rect widths).
        height: Flag height.

    Returns:
        An SVG fragment containing three ``<rect>`` elements.
    """
    side_width: int = round(width * 0.25)
    centre_width: int = width - 2 * side_width
    return (
        f'<rect x="{x}" y="{y}" width="{side_width}" height="{height}" fill="#D52B1E"/>'
        f'<rect x="{x + side_width}" y="{y}" width="{centre_width}" height="{height}" fill="#FFFFFF"/>'
        f'<rect x="{x + side_width + centre_width}" y="{y}" width="{side_width}" height="{height}" fill="#D52B1E"/>'
    )


def compose_svg(
    about: dict[str, Any],
    system_info: dict[str, Any],
    tech_stack: dict[str, Any],
    connect: dict[str, Any],
) -> str:
    """Compose the complete dashboard-top SVG as a single string.

    Reads icon and font assets from the standard paths defined as module
    constants. The portrait PNG is base64-embedded if present; if missing,
    the portrait card region renders as a placeholder rect (build still
    succeeds for headless test environments).

    Args:
        about: Parsed ``content/about.yml``.
        system_info: Parsed ``content/system_info.yml``.
        tech_stack: Parsed ``content/tech_stack.yml``.
        connect: Parsed ``content/connect.yml``.

    Returns:
        A complete SVG document string suitable for writing to disk.
    """
    parts: list[str] = []
    parts.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1500 880">')
    parts.append(f'<rect x="0" y="0" width="1500" height="880" fill="{BG}"/>')

    # Hero strip (outlined headline + role tags + lime cursor)
    headline_d: str = outline("Dinesh Dawonauth", INTER_BOLD, size_px=36)
    parts.append(
        f'<g transform="translate(30,68)" fill="{TEXT}">'
        f'<path d="{headline_d}"/>'
        f'</g>'
    )
    parts.append(
        f'<text x="380" y="64" font-family="monospace" font-size="28" fill="{ACCENT}">&gt;_</text>'
    )
    role_d: str = outline("AI Engineer · Developer · Builder", INTER_MEDIUM, size_px=16)
    parts.append(
        f'<g transform="translate(30,90)" fill="{ACCENT}">'
        f'<path d="{role_d}"/>'
        f'</g>'
    )

    # Profile card (base64 portrait PNG if available, placeholder otherwise)
    if PORTRAIT_PATH.exists():
        b64: str = base64.b64encode(PORTRAIT_PATH.read_bytes()).decode("ascii")
        parts.append(
            f'<image x="30" y="110" width="400" height="530" '
            f'href="data:image/png;base64,{b64}" preserveAspectRatio="xMidYMid slice"/>'
        )
    else:
        parts.append(
            f'<rect x="30" y="110" width="400" height="530" '
            f'fill="{SURFACE}" stroke="{BORDER}" rx="12"/>'
        )

    # Quote block (under portrait)
    parts.append(
        f'<text x="30" y="685" font-family="monospace" font-size="13" fill="{TEXT_MUTED}">'
        f'<tspan>"Shipping love into production since </tspan>'
        f'<tspan fill="{ACCENT}">2018</tspan><tspan>."</tspan>'
        f'</text>'
    )

    # ABOUT ME panel
    parts.append(_about_panel(about))

    # System info column
    parts.append(_system_info_column(system_info))

    # TECH I WORK WITH strip
    parts.append(_tech_strip(tech_stack))

    # CONNECT block
    parts.append(_connect_block(connect))

    # Build CTA line
    cta: str = (
        f'<text x="30" y="870" font-family="monospace" font-size="13" fill="{TEXT_MUTED}">'
        f'<tspan fill="{ACCENT}">&gt; </tspan>'
        f'<tspan>Let’s build something </tspan>'
        f'<tspan fill="{ACCENT}">meaningful</tspan>'
        f'<tspan> together.</tspan>'
        f'</text>'
    )
    parts.append(cta)

    parts.append("</svg>")
    return "".join(parts)


def _about_panel(about: dict[str, Any]) -> str:
    """Render the ABOUT ME panel with header, bio lines, and trait pills.

    Args:
        about: Parsed ``content/about.yml``.

    Returns:
        An SVG fragment string.
    """
    icon_path: Path = UI_ICONS_DIR / "user.svg"
    parts: list[str] = []
    parts.append(embed_icon(icon_path, x=460, y=128, size=18))
    header_d: str = outline("ABOUT ME", INTER_BOLD, size_px=14)
    parts.append(
        f'<g transform="translate(488,142)" fill="{ACCENT}">'
        f'<path d="{header_d}"/>'
        f'</g>'
    )
    for line_index, line in enumerate(about.get("bio", [])):
        line_y: int = 180 + line_index * 22
        parts.append(
            f'<text x="460" y="{line_y}" font-family="monospace" '
            f'font-size="13" fill="{TEXT}">{line}</text>'
        )
    pill_origin_y: int = 180 + len(about.get("bio", [])) * 22 + 30
    pill_origin_x: int = 460
    pill_width: int = 140
    pill_x_stride: int = pill_width + 12
    pill_row_stride: int = 30
    for pill_index, pill in enumerate(about.get("trait_pills", [])):
        col: int = pill_index % 2
        row: int = pill_index // 2
        pill_x: int = pill_origin_x + col * pill_x_stride
        pill_y: int = pill_origin_y + row * pill_row_stride
        parts.append(
            f'<rect x="{pill_x}" y="{pill_y - 16}" width="{pill_width}" height="26" '
            f'rx="13" fill="{SURFACE}" stroke="{BORDER}"/>'
        )
        pill_icon: Path = UI_ICONS_DIR / f"{pill['icon']}.svg"
        parts.append(embed_icon(pill_icon, x=pill_x + 8, y=pill_y - 12, size=14))
        parts.append(
            f'<text x="{pill_x + 28}" y="{pill_y + 1}" font-family="monospace" '
            f'font-size="11" fill="{TEXT}">{pill["label"]}</text>'
        )
    return "".join(parts)


def _system_info_column(system_info: dict[str, Any]) -> str:
    """Render the system info column of icon+label+value rows.

    Args:
        system_info: Parsed ``content/system_info.yml``.

    Returns:
        An SVG fragment string.
    """
    parts: list[str] = []
    for row_index, row in enumerate(system_info.get("rows", [])):
        row_y: int = 140 + row_index * 28
        icon_path: Path = UI_ICONS_DIR / f"{row['icon']}.svg"
        parts.append(
            label_value_row(
                icon_path=icon_path,
                x=900,
                y=row_y,
                label=row["label"],
                value=row["value"],
            )
        )
        if row.get("flag") == "CA":
            parts.append(canada_flag(x=900 + 280, y=row_y - 9, width=15, height=10))
    return "".join(parts)


def _tech_strip(tech_stack: dict[str, Any]) -> str:
    """Render the TECH I WORK WITH icon strip.

    Args:
        tech_stack: Parsed ``content/tech_stack.yml``.

    Returns:
        An SVG fragment string.
    """
    parts: list[str] = []
    parts.append(embed_icon(UI_ICONS_DIR / "terminal.svg", x=460, y=408, size=18))
    header_d: str = outline("TECH I WORK WITH", INTER_BOLD, size_px=14)
    parts.append(
        f'<g transform="translate(488,422)" fill="{ACCENT}">'
        f'<path d="{header_d}"/>'
        f'</g>'
    )
    icons: list[dict[str, str]] = tech_stack.get("icons", [])
    if not icons:
        return "".join(parts)
    column_width: int = (1470 - 460) // len(icons)
    for index, icon_info in enumerate(icons):
        icon_path: Path = TECH_ICONS_DIR / icon_info["file"]
        cx: int = 460 + index * column_width + (column_width - 56) // 2
        parts.append(embed_icon(icon_path, x=cx, y=460, size=56))
        parts.append(
            f'<text x="{cx + 28}" y="540" font-family="monospace" '
            f'font-size="11" fill="{TEXT_MUTED}" text-anchor="middle">{icon_info["label"]}</text>'
        )
    return "".join(parts)


def _connect_block(connect: dict[str, Any]) -> str:
    """Render the CONNECT block with icon+label rows.

    Args:
        connect: Parsed ``content/connect.yml``.

    Returns:
        An SVG fragment string.
    """
    parts: list[str] = []
    header_d: str = outline("CONNECT", INTER_BOLD, size_px=12)
    parts.append(
        f'<g transform="translate(30,725)" fill="{ACCENT}">'
        f'<path d="{header_d}"/>'
        f'</g>'
    )
    for row_index, row in enumerate(connect.get("rows", [])):
        row_y: int = 752 + row_index * 22
        icon_path: Path = UI_ICONS_DIR / f"{row['icon']}.svg"
        parts.append(embed_icon(icon_path, x=30, y=row_y - 12, size=14))
        parts.append(
            f'<text x="52" y="{row_y}" font-family="monospace" '
            f'font-size="12" fill="{TEXT_MUTED}">{row["label"]}</text>'
        )
    return "".join(parts)


def main() -> int:
    """Read content YAMLs, compose the SVG, write the output file.

    Returns:
        ``0`` on success, ``1`` on any handled failure.
    """
    try:
        about = yaml.safe_load((CONTENT_DIR / "about.yml").read_text(encoding="utf-8"))
        system_info = yaml.safe_load(
            (CONTENT_DIR / "system_info.yml").read_text(encoding="utf-8")
        )
        tech_stack = yaml.safe_load(
            (CONTENT_DIR / "tech_stack.yml").read_text(encoding="utf-8")
        )
        connect = yaml.safe_load(
            (CONTENT_DIR / "connect.yml").read_text(encoding="utf-8")
        )
        svg = compose_svg(about, system_info, tech_stack, connect)
        OUTPUT_PATH.write_text(svg, encoding="utf-8")
    except (FileNotFoundError, ValueError, yaml.YAMLError) as exc:
        sys.stderr.write(f"build_dashboard_top: {exc}\n")
        return 1
    sys.stdout.write(f"build_dashboard_top: wrote {OUTPUT_PATH}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
