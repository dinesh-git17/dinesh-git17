"""Marker-bounded SVG patching utilities.

Two patch strategies are supported:

* :func:`patch_marker` rewrites text content bounded by a comment-marker pair
  (``<!-- KEY_START -->VALUE<!-- KEY_END -->``). Use this for any value that
  lives inside a ``<text>`` element or other text node.
* :func:`patch_element_attribute` rewrites an attribute value on an element
  identified by its ``id``. Use this for SVG attribute values that vary at
  refresh time, such as ``stroke-dasharray`` on a progress ring or ``width``
  on a language bar. XML comments are illegal inside attribute values, so the
  comment-marker strategy cannot be used there.

Both patches are idempotent — if the new value matches the existing value, no
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


def patch_element_attribute(
    svg_path: Path,
    element_id: str,
    attr_name: str,
    new_value: str,
) -> bool:
    """Replace ``attr_name`` on the element whose ``id`` matches ``element_id``.

    Args:
        svg_path: Path to the SVG file containing the target element.
        element_id: The value of the element's ``id`` attribute (e.g.
            ``"grade-ring"``).
        attr_name: The name of the attribute to rewrite (e.g.
            ``"stroke-dasharray"``).
        new_value: The replacement attribute value. Inserted verbatim between
            the surrounding double quotes.

    Returns:
        ``True`` if the file was rewritten, ``False`` if the value already
        matched and no write was necessary.

    Raises:
        FileNotFoundError: If ``svg_path`` does not exist.
        ValueError: If no element with the given id is found, or if the
            element does not carry the named attribute.
    """
    content: str = svg_path.read_text(encoding="utf-8")

    tag_pattern: re.Pattern[str] = re.compile(
        rf'<[^>]*\sid="{re.escape(element_id)}"[^>]*>'
    )
    tag_match: re.Match[str] | None = tag_pattern.search(content)
    if tag_match is None:
        msg = f"element with id={element_id!r} not found in {svg_path}"
        raise ValueError(msg)

    tag: str = tag_match.group(0)
    attr_pattern: re.Pattern[str] = re.compile(rf'\s{re.escape(attr_name)}="([^"]*)"')
    attr_match: re.Match[str] | None = attr_pattern.search(tag)
    if attr_match is None:
        msg = (
            f"attribute {attr_name!r} not found on element id={element_id!r} "
            f"in {svg_path}"
        )
        raise ValueError(msg)

    if attr_match.group(1) == new_value:
        return False

    new_tag: str = attr_pattern.sub(f' {attr_name}="{new_value}"', tag, count=1)
    new_content: str = (
        content[: tag_match.start()] + new_tag + content[tag_match.end() :]
    )
    svg_path.write_text(new_content, encoding="utf-8")
    return True
