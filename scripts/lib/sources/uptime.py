"""Uptime source: years-and-months elapsed since EPOCH."""

from dataclasses import dataclass
from datetime import date

EPOCH: date = date(2023, 9, 1)


@dataclass(frozen=True)
class UptimeResult:
    """Result of an uptime fetch."""

    value: str


def fetch(*, today: date | None = None) -> UptimeResult:
    """Return the elapsed time between EPOCH and today as ``"N years, M months"``.

    Args:
        today: Reference date. Defaults to ``date.today()`` when omitted.

    Returns:
        The formatted result.

    Raises:
        ValueError: If ``today`` is earlier than EPOCH.
    """
    today = today if today is not None else date.today()
    if today < EPOCH:
        msg = f"today ({today}) is earlier than epoch ({EPOCH})"
        raise ValueError(msg)
    years: int = today.year - EPOCH.year
    months: int = today.month - EPOCH.month
    if months < 0:
        years -= 1
        months += 12
    return UptimeResult(value=f"{years} years, {months} months")
