"""Shared SVG construction helpers used by the dashboard composer.

The icon embed helper inlines a Lucide-style or brand SVG by stripping the
outer ``<svg>`` element and wrapping the inner content in a translate+scale
``<g>``. Presentation attributes set on the icon's root (``stroke``,
``fill``, ``stroke-width``, ``stroke-linecap``, ``stroke-linejoin``) are
forwarded onto the wrapping ``<g>`` so children that rely on inheritance
(every Lucide outline icon) render correctly. Brand icons (Simple Icons,
Devicon) that paint with path-level ``fill`` are unaffected.
"""

import re
from pathlib import Path

_INHERITABLE_ICON_ATTRS: tuple[str, ...] = (
    "fill",
    "stroke",
    "stroke-width",
    "stroke-linecap",
    "stroke-linejoin",
)


def embed_icon(
    icon_path: Path,
    x: float,
    y: float,
    size: float,
    stroke: str | None = None,
    fill: str | None = None,
) -> str:
    """Return a ``<g>`` element that embeds an icon's inner SVG content.

    Args:
        icon_path: Path to the source SVG icon.
        x: Target x position (top-left of the icon in the parent SVG).
        y: Target y position.
        size: Target rendered size in pixels (square).
        stroke: Optional override for the inherited ``stroke`` colour. When
            set, replaces whatever stroke value the source icon declares so
            the same outline icon can be reused in different colours.
        fill: Optional override for the inherited ``fill`` colour. Mirror of
            ``stroke`` for filled (brand) icons whose root carries the colour.

    Returns:
        An SVG ``<g>`` element string positioned at (``x``, ``y``) with
        scale chosen so the icon's source viewBox maps to ``size`` pixels.

    Raises:
        FileNotFoundError: If ``icon_path`` does not exist.
        ValueError: If the icon does not contain a ``viewBox`` attribute or
            an ``<svg>`` root element.
    """
    content: str = icon_path.read_text(encoding="utf-8")
    viewbox_match: re.Match[str] | None = re.search(r'viewBox\s*=\s*"([^"]+)"', content)
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
            value: str = attr_match.group(1)
            if attr == "stroke" and stroke is not None and value != "none":
                value = stroke
            elif attr == "fill" and fill is not None and value != "none":
                value = fill
            inherited.append(f'{attr}="{value}"')
    if stroke is not None and not any(a.startswith("stroke=") for a in inherited):
        inherited.append(f'stroke="{stroke}"')
    if fill is not None and not any(a.startswith("fill=") for a in inherited):
        inherited.append(f'fill="{fill}"')

    inner_match: re.Match[str] | None = re.search(
        r"<svg[^>]*>(.*)</svg>", content, re.DOTALL
    )
    if inner_match is None:
        msg = f"icon {icon_path.name} has no closing </svg>"
        raise ValueError(msg)
    inner: str = inner_match.group(1).strip()

    inherited_attrs: str = (" " + " ".join(inherited)) if inherited else ""
    return (
        f'<g transform="translate({x:g},{y:g}) scale({scale:.4f})"'
        f"{inherited_attrs}>{inner}</g>"
    )
