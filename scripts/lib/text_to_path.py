"""Convert text strings into SVG path data using vendored fonts.

GitHub's SVG sanitiser strips ``<style>`` blocks and ``@font-face``
declarations, which means custom fonts cannot be loaded at render time. To
preserve display typography (the hero headline, section headers, big stat
numbers), this module converts each string into ``<path d="...">`` data
using ``fonttools``. The resulting paths render identically across all
viewers, at the cost of being non-selectable and non-searchable.
"""

from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont


def outline(text: str, font_path: Path, size_px: int) -> str:
    """Return SVG path data representing ``text`` rendered in the given font.

    Glyphs are positioned left-to-right starting at the SVG origin, with
    each glyph's advance width applied as horizontal offset. The y-axis is
    flipped from the font's y-up coordinate system to SVG's y-down system,
    with the baseline placed at ``size_px``. The returned ``d`` attribute
    value can be embedded directly into a ``<path>`` element.

    Args:
        text: The string to outline. Must contain only glyphs present in
            the font.
        font_path: Path to a TTF or OTF font file.
        size_px: The target font size in CSS pixels. The font's units-per-em
            is rescaled to this size.

    Returns:
        SVG path data (the value for a ``d`` attribute), starting with a
        moveTo command.

    Raises:
        FileNotFoundError: If ``font_path`` does not exist.
        ValueError: If ``text`` contains a character with no glyph in the
            font.
    """
    if not font_path.exists():
        raise FileNotFoundError(f"font file not found: {font_path}")

    font: TTFont = TTFont(str(font_path))
    cmap: dict[int, str] = font.getBestCmap()
    glyph_set = font.getGlyphSet()
    units_per_em: int = font["head"].unitsPerEm
    scale: float = size_px / units_per_em

    pen = SVGPathPen(glyph_set)
    cursor_x: float = 0.0

    for char in text:
        codepoint: int = ord(char)
        if codepoint not in cmap:
            msg = f"font {font_path.name} has no glyph for {char!r} (U+{codepoint:04X})"
            raise ValueError(msg)
        glyph_name: str = cmap[codepoint]
        glyph = glyph_set[glyph_name]
        # Transform: scale x, flip y (font is y-up; SVG is y-down), offset x.
        # Baseline is placed at size_px so glyphs appear in positive y space.
        transform = (scale, 0, 0, -scale, cursor_x, float(size_px))
        tp = TransformPen(pen, transform)
        glyph.draw(tp)
        cursor_x += glyph.width * scale

    return pen.getCommands()
