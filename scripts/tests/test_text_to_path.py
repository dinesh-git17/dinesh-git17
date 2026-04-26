"""Tests for the text-to-SVG-path outliner."""

from pathlib import Path

import pytest

from scripts.lib.text_to_path import outline


@pytest.fixture
def inter_bold(repo_root: Path) -> Path:
    return repo_root / "scripts" / "fonts" / "Inter" / "Inter-Bold.otf"


def test_outline_returns_non_empty_path_data(inter_bold: Path) -> None:
    path_d = outline("A", inter_bold, size_px=48)
    assert isinstance(path_d, str)
    assert path_d.startswith("M")
    assert len(path_d) > 20


def test_outline_is_deterministic(inter_bold: Path) -> None:
    first = outline("Dinesh", inter_bold, size_px=48)
    second = outline("Dinesh", inter_bold, size_px=48)
    assert first == second


def test_outline_raises_on_missing_glyph(inter_bold: Path) -> None:
    with pytest.raises(ValueError, match="no glyph"):
        outline("香", inter_bold, size_px=48)


def test_outline_raises_when_font_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        outline("A", tmp_path / "missing.otf", size_px=48)
