"""Patch the uptime value inside assets/neofetch.svg.

Idempotent: rewrites the file only when the computed uptime string differs
from the current value between the UPTIME_START / UPTIME_END markers.
"""

import re
import sys
from datetime import date
from pathlib import Path

REPO_ROOT: Path = Path(__file__).resolve().parent.parent
SVG_PATH: Path = REPO_ROOT / "assets" / "neofetch.svg"
EPOCH: date = date(2018, 9, 1)
MARKER_PATTERN: re.Pattern[str] = re.compile(
    r"<!-- UPTIME_START -->(.*?)<!-- UPTIME_END -->",
    re.DOTALL,
)


def compute_uptime(epoch: date, today: date) -> str:
    """Return the elapsed time between two dates in "N years, M months" form.

    Args:
        epoch: The start date.
        today: The reference date (usually ``date.today()``).

    Returns:
        A string like ``"7 years, 7 months"``. The month count always lies
        in the range ``[0, 11]``.

    Raises:
        ValueError: If ``today`` is earlier than ``epoch``.
    """
    if today < epoch:
        msg = f"today ({today}) is earlier than epoch ({epoch})"
        raise ValueError(msg)
    years: int = today.year - epoch.year
    months: int = today.month - epoch.month
    if months < 0:
        years -= 1
        months += 12
    return f"{years} years, {months} months"


def patch_svg(svg_path: Path, new_uptime: str) -> bool:
    """Replace the UPTIME marker content in the SVG file in place.

    Args:
        svg_path: Path to the SVG file containing the markers.
        new_uptime: The value to embed between the markers.

    Returns:
        ``True`` if the file was rewritten, ``False`` if the value already
        matched and no write was necessary.

    Raises:
        FileNotFoundError: If ``svg_path`` does not exist.
        ValueError: If the SVG does not contain both UPTIME markers.
    """
    content: str = svg_path.read_text(encoding="utf-8")
    match: re.Match[str] | None = MARKER_PATTERN.search(content)
    if match is None:
        msg = f"UPTIME markers not found in {svg_path}"
        raise ValueError(msg)
    if match.group(1) == new_uptime:
        return False
    replacement: str = f"<!-- UPTIME_START -->{new_uptime}<!-- UPTIME_END -->"
    svg_path.write_text(MARKER_PATTERN.sub(replacement, content), encoding="utf-8")
    return True


def main() -> int:
    """Entry point: compute uptime and patch the SVG if needed.

    Returns:
        Process exit code. ``0`` on success (whether or not a write
        occurred), ``1`` on any handled failure.
    """
    try:
        uptime: str = compute_uptime(EPOCH, date.today())
        changed: bool = patch_svg(SVG_PATH, uptime)
    except (FileNotFoundError, ValueError) as exc:
        sys.stderr.write(f"update_uptime: {exc}\n")
        return 1
    if changed:
        sys.stdout.write(f"update_uptime: set uptime to {uptime}\n")
    else:
        sys.stdout.write(f"update_uptime: no change (already {uptime})\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
