"""Build the unified GitHub profile dashboard SVG.

Composes a single 1500x1000 canvas with one outer rounded frame, a left
sidebar of four cards (portrait / quote / connect / CTA), and a right
column of four sections (top panel / tech strip / stats row / enjoy
strip). Reads content from ``content/*.yml`` and writes the result to
``assets/dashboard.svg``.

Run manually when content changes. The daily Action only patches
marker-bounded values inside the produced SVG.
"""

import sys
from pathlib import Path
from typing import Any

import yaml

from scripts.lib import dashboard_layout as L

REPO_ROOT: Path = Path(__file__).resolve().parent.parent
CONTENT_DIR: Path = REPO_ROOT / "content"
OUTPUT_PATH: Path = REPO_ROOT / "assets" / "dashboard.svg"


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
    parts.append(L.panel(L.QUOTE_CARD))
    parts.append(L.panel(L.CONNECT_CARD))
    parts.append(L.panel(L.CTA_CARD))
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
