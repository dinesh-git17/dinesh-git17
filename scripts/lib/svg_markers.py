"""Marker-bounded SVG patching utilities.

Every dynamic value in the dashboard SVGs lives between an XML comment marker
pair: ``<!-- KEY_START -->VALUE<!-- KEY_END -->``. These helpers rewrite the
value in place while preserving the rest of the file byte-for-byte.

All patches are idempotent — if the new value matches the existing value, no
write occurs and the function returns ``False``.
"""

import re
from pathlib import Path


def patch_marker(svg_path: Path, key: str, new_value: str) -> bool:
    """Replace the value bounded by ``KEY_START`` / ``KEY_END`` markers.

    Args:
        svg_path: Path to the SVG file containing the marker pair.
        key: The marker key (e.g. ``"STARS"``). The literal markers
            ``<!-- {key}_START -->`` and ``<!-- {key}_END -->`` must both
            exist in the file.
        new_value: The replacement string. Inserted verbatim between the
            markers. May be empty.

    Returns:
        ``True`` if the file was rewritten, ``False`` if the value already
        matched and no write was necessary.

    Raises:
        FileNotFoundError: If ``svg_path`` does not exist.
        ValueError: If both markers are not found in the file.
    """
    pattern: re.Pattern[str] = re.compile(
        rf"<!-- {re.escape(key)}_START -->(.*?)<!-- {re.escape(key)}_END -->",
        re.DOTALL,
    )
    content: str = svg_path.read_text(encoding="utf-8")
    match: re.Match[str] | None = pattern.search(content)
    if match is None:
        msg = f"marker pair {key}_START / {key}_END not found in {svg_path}"
        raise ValueError(msg)
    if match.group(1) == new_value:
        return False
    replacement: str = f"<!-- {key}_START -->{new_value}<!-- {key}_END -->"
    svg_path.write_text(pattern.sub(replacement, content), encoding="utf-8")
    return True


def patch_attribute_marker(svg_path: Path, key: str, new_value: str) -> bool:
    """Replace a value inside an attribute-bound marker pair.

    Used for SVG attribute values that need to vary at refresh time, such as
    ``stroke-dasharray`` on the streak ring or ``width`` on a language bar.
    The marker pair is identical to :func:`patch_marker`; only the embedding
    context differs (inside an attribute value rather than text content).

    Args:
        svg_path: Path to the SVG file containing the marker pair.
        key: The marker key (e.g. ``"STREAK_RING_DASHARRAY"``).
        new_value: The replacement attribute value (e.g. ``"180 360"``).

    Returns:
        ``True`` if the file was rewritten, ``False`` if unchanged.

    Raises:
        FileNotFoundError: If ``svg_path`` does not exist.
        ValueError: If both markers are not found in the file.
    """
    return patch_marker(svg_path, key, new_value)
