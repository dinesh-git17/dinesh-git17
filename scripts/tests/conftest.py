"""Shared pytest fixtures for the dashboard build and fetcher test suites."""

from pathlib import Path

import pytest

REPO_ROOT: Path = Path(__file__).resolve().parent.parent.parent


@pytest.fixture
def repo_root() -> Path:
    """Return the absolute path to the repository root."""
    return REPO_ROOT


@pytest.fixture
def fixtures_dir() -> Path:
    """Return the absolute path to the test fixtures directory."""
    return Path(__file__).resolve().parent / "fixtures"
