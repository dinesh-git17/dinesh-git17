"""Rewrite the cache-buster ``v`` query param on the stats card URLs in README.md.

Runs idempotently per-day on schedule (rolls the date over), and bumps the
monotonic suffix on manual dispatches to flush the Vercel and camo caches.
"""

import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

REPO_ROOT: Path = Path(__file__).resolve().parent.parent
README_PATH: Path = REPO_ROOT / "README.md"
EXPECTED_URL_COUNT: int = 3

URL_PATTERN: re.Pattern[str] = re.compile(
    r"https://github-readme-(?:stats-inky-three-53|streak-stats-ivory-eta-73)"
    r"\.vercel\.app[^\s\"'<>]+"
)
V_PATTERN: re.Pattern[str] = re.compile(
    r"^(?P<date>\d{4}-\d{2}-\d{2})\.(?P<n>\d+)$"
)


def main() -> int:
    """Entry point. Returns process exit code."""
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
