"""Tests for the marker-bounded SVG patching utilities."""

from pathlib import Path

import pytest

from scripts.lib.svg_markers import patch_element_attribute, patch_marker


def test_patch_marker_replaces_value(tmp_path: Path) -> None:
    svg = tmp_path / "test.svg"
    svg.write_text(
        '<svg><text>before <!-- STARS_START -->100<!-- STARS_END --> after</text></svg>',
        encoding="utf-8",
    )
    changed = patch_marker(svg, "STARS", "999")
    assert changed is True
    content = svg.read_text(encoding="utf-8")
    assert "<!-- STARS_START -->999<!-- STARS_END -->" in content
    assert "100" not in content


def test_patch_marker_returns_false_when_unchanged(tmp_path: Path) -> None:
    svg = tmp_path / "test.svg"
    original = '<svg><text><!-- COMMITS_START -->42<!-- COMMITS_END --></text></svg>'
    svg.write_text(original, encoding="utf-8")
    mtime_before = svg.stat().st_mtime_ns
    changed = patch_marker(svg, "COMMITS", "42")
    assert changed is False
    assert svg.stat().st_mtime_ns == mtime_before
    assert svg.read_text(encoding="utf-8") == original


def test_patch_marker_raises_when_marker_missing(tmp_path: Path) -> None:
    svg = tmp_path / "test.svg"
    svg.write_text("<svg><text>no markers here</text></svg>", encoding="utf-8")
    with pytest.raises(ValueError, match="marker pair STARS_START / STARS_END not found"):
        patch_marker(svg, "STARS", "100")


def test_patch_marker_handles_multiple_markers_in_same_file(tmp_path: Path) -> None:
    svg = tmp_path / "test.svg"
    svg.write_text(
        '<svg><text><!-- A_START -->1<!-- A_END --> '
        '<!-- B_START -->2<!-- B_END --></text></svg>',
        encoding="utf-8",
    )
    assert patch_marker(svg, "A", "10") is True
    content = svg.read_text(encoding="utf-8")
    assert "<!-- A_START -->10<!-- A_END -->" in content
    assert "<!-- B_START -->2<!-- B_END -->" in content
    assert patch_marker(svg, "B", "20") is True
    content = svg.read_text(encoding="utf-8")
    assert "<!-- A_START -->10<!-- A_END -->" in content
    assert "<!-- B_START -->20<!-- B_END -->" in content


def test_patch_element_attribute_replaces_value(tmp_path: Path) -> None:
    svg = tmp_path / "test.svg"
    svg.write_text(
        '<svg><circle id="grade-ring" cx="50" cy="50" r="40" '
        'stroke-dasharray="100 250" stroke="lime"/></svg>',
        encoding="utf-8",
    )
    changed = patch_element_attribute(svg, "grade-ring", "stroke-dasharray", "180 250")
    assert changed is True
    content = svg.read_text(encoding="utf-8")
    assert 'stroke-dasharray="180 250"' in content
    assert 'id="grade-ring"' in content
    assert "100 250" not in content


def test_patch_element_attribute_returns_false_when_unchanged(tmp_path: Path) -> None:
    svg = tmp_path / "test.svg"
    original = '<svg><rect id="bar-1" width="120" height="12"/></svg>'
    svg.write_text(original, encoding="utf-8")
    mtime_before = svg.stat().st_mtime_ns
    changed = patch_element_attribute(svg, "bar-1", "width", "120")
    assert changed is False
    assert svg.stat().st_mtime_ns == mtime_before
    assert svg.read_text(encoding="utf-8") == original


def test_patch_element_attribute_raises_when_id_missing(tmp_path: Path) -> None:
    svg = tmp_path / "test.svg"
    svg.write_text('<svg><rect width="50"/></svg>', encoding="utf-8")
    with pytest.raises(ValueError, match="element with id='nope' not found"):
        patch_element_attribute(svg, "nope", "width", "100")


def test_patch_element_attribute_raises_when_attribute_missing(tmp_path: Path) -> None:
    svg = tmp_path / "test.svg"
    svg.write_text('<svg><rect id="bar-1" width="50"/></svg>', encoding="utf-8")
    with pytest.raises(ValueError, match="attribute 'height' not found on element id='bar-1'"):
        patch_element_attribute(svg, "bar-1", "height", "12")


def test_patch_element_attribute_only_touches_matching_element(tmp_path: Path) -> None:
    svg = tmp_path / "test.svg"
    svg.write_text(
        '<svg>'
        '<rect id="bar-1" width="50" height="12"/>'
        '<rect id="bar-2" width="50" height="12"/>'
        '</svg>',
        encoding="utf-8",
    )
    assert patch_element_attribute(svg, "bar-2", "width", "200") is True
    content = svg.read_text(encoding="utf-8")
    assert '<rect id="bar-1" width="50" height="12"/>' in content
    assert '<rect id="bar-2" width="200" height="12"/>' in content
