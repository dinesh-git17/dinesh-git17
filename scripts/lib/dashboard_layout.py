"""Layout constants and panel primitives for the unified dashboard SVG.

The dashboard is composed as a single 1500x1000 canvas with one outer
rounded frame, a left sidebar of four cards, and a right column of four
sections (top panel / tech strip / stats row / enjoy strip). All
coordinates derive from the canvas dimensions plus padding/gutter
constants so geometry can be tuned in one place.
"""

from typing import NamedTuple

CANVAS_W: int = 1500
CANVAS_H: int = 1000
OUTER_PAD: int = 16
INNER_PAD: int = 16
GUTTER: int = 16
SIDEBAR_W: int = 320
PANEL_RADIUS: int = 12
OUTER_FRAME_RADIUS: int = 16

BG: str = "#0A0E1A"
SURFACE: str = "#11151F"
SURFACE_2: str = "#161B28"
BORDER: str = "#1F2533"
TRACK: str = "#262C3A"
ACCENT: str = "#9EFF5A"
ACCENT_DIM: str = "#6BBF3D"
TEXT: str = "#E8E8E0"
TEXT_MUTED: str = "#8B92A5"


class Rect(NamedTuple):
    """Axis-aligned rectangle in SVG coordinates."""

    x: int
    y: int
    w: int
    h: int

    @property
    def right(self) -> int:
        return self.x + self.w

    @property
    def bottom(self) -> int:
        return self.y + self.h

    @property
    def cx(self) -> int:
        return self.x + self.w // 2

    @property
    def cy(self) -> int:
        return self.y + self.h // 2


CONTENT_X: int = OUTER_PAD + INNER_PAD
CONTENT_Y: int = OUTER_PAD + INNER_PAD
CONTENT_W: int = CANVAS_W - 2 * (OUTER_PAD + INNER_PAD)
CONTENT_H: int = CANVAS_H - 2 * (OUTER_PAD + INNER_PAD)

OUTER_FRAME: Rect = Rect(OUTER_PAD, OUTER_PAD, CANVAS_W - 2 * OUTER_PAD, CANVAS_H - 2 * OUTER_PAD)

PORTRAIT_H: int = 420
QUOTE_H: int = 110
CONNECT_H: int = 180
CTA_H: int = CONTENT_H - PORTRAIT_H - QUOTE_H - CONNECT_H - 3 * GUTTER

PORTRAIT_CARD: Rect = Rect(CONTENT_X, CONTENT_Y, SIDEBAR_W, PORTRAIT_H)
QUOTE_CARD: Rect = Rect(CONTENT_X, PORTRAIT_CARD.bottom + GUTTER, SIDEBAR_W, QUOTE_H)
CONNECT_CARD: Rect = Rect(CONTENT_X, QUOTE_CARD.bottom + GUTTER, SIDEBAR_W, CONNECT_H)
CTA_CARD: Rect = Rect(CONTENT_X, CONNECT_CARD.bottom + GUTTER, SIDEBAR_W, CTA_H)

RIGHT_X: int = CONTENT_X + SIDEBAR_W + GUTTER
RIGHT_W: int = CONTENT_W - SIDEBAR_W - GUTTER

TOP_PANEL_H: int = 270
TECH_PANEL_H: int = 170
STATS_ROW_H: int = 270
ENJOY_PANEL_H: int = CONTENT_H - TOP_PANEL_H - TECH_PANEL_H - STATS_ROW_H - 3 * GUTTER

TOP_PANEL: Rect = Rect(RIGHT_X, CONTENT_Y, RIGHT_W, TOP_PANEL_H)
TECH_PANEL: Rect = Rect(RIGHT_X, TOP_PANEL.bottom + GUTTER, RIGHT_W, TECH_PANEL_H)
STATS_ROW: Rect = Rect(RIGHT_X, TECH_PANEL.bottom + GUTTER, RIGHT_W, STATS_ROW_H)
ENJOY_PANEL: Rect = Rect(RIGHT_X, STATS_ROW.bottom + GUTTER, RIGHT_W, ENJOY_PANEL_H)

STATS_CARD_W: int = (RIGHT_W - 2 * GUTTER) // 3
STATS_GLANCE: Rect = Rect(RIGHT_X, STATS_ROW.y, STATS_CARD_W, STATS_ROW_H)
STATS_CONTRIB: Rect = Rect(STATS_GLANCE.right + GUTTER, STATS_ROW.y, STATS_CARD_W, STATS_ROW_H)
STATS_LANGS: Rect = Rect(STATS_CONTRIB.right + GUTTER, STATS_ROW.y, STATS_CARD_W, STATS_ROW_H)


def panel(
    rect: Rect,
    fill: str = SURFACE,
    stroke: str = BORDER,
    radius: int = PANEL_RADIUS,
) -> str:
    """Return a single rounded ``<rect>`` element for a panel background.

    Args:
        rect: Panel position and size.
        fill: Panel fill colour.
        stroke: Panel stroke colour.
        radius: Corner radius in pixels.

    Returns:
        An SVG ``<rect>`` element string.
    """
    return (
        f'<rect x="{rect.x}" y="{rect.y}" width="{rect.w}" height="{rect.h}" '
        f'rx="{radius}" fill="{fill}" stroke="{stroke}"/>'
    )


def outer_frame() -> str:
    """Return the outermost rounded border that wraps every dashboard panel.

    The frame has no fill (the canvas background shows through) and a
    single ``BORDER``-coloured stroke just inside the canvas edge.

    Returns:
        An SVG ``<rect>`` element string.
    """
    r: Rect = OUTER_FRAME
    return (
        f'<rect x="{r.x}" y="{r.y}" width="{r.w}" height="{r.h}" '
        f'rx="{OUTER_FRAME_RADIUS}" fill="none" stroke="{BORDER}"/>'
    )


def canvas_background() -> str:
    """Return the full-bleed canvas background rect.

    Returns:
        An SVG ``<rect>`` element string covering the entire viewBox.
    """
    return f'<rect x="0" y="0" width="{CANVAS_W}" height="{CANVAS_H}" fill="{BG}"/>'


def svg_open() -> str:
    """Return the opening ``<svg>`` tag with the canvas viewBox."""
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CANVAS_W} {CANVAS_H}">'
