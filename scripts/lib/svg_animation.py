"""Native SVG SMIL animation primitives for the dashboard build.

All emitters return self-closed SVG fragment strings that can be
concatenated into the larger SVG document produced by
``scripts.build_dashboard``. Boot animations use ``fill="freeze"`` so
the animated final state persists; idle animations loop with
``repeatCount="indefinite"`` and return to the baseline each cycle.

Timing constants below define the coordinated boot sequence described
in ``docs/superpowers/specs/2026-04-26-dashboard-animation-design.md``.
Tune values here when adjusting the load feel.
"""

from typing import Final

BOOT_PROMPT_BEGIN_S: Final[float] = 0.2
BOOT_TECH_BEGIN_S: Final[float] = 0.5
BOOT_TECH_STAGGER_S: Final[float] = 0.14
BOOT_TECH_DUR_S: Final[float] = 0.9
BOOT_STATS_BEGIN_S: Final[float] = 1.3
BOOT_STATS_STAGGER_S: Final[float] = 0.18
BOOT_STATS_DUR_S: Final[float] = 1.1
BOOT_RING_DUR_S: Final[float] = 1.4
BOOT_NUMBER_DUR_S: Final[float] = 0.9
IDLE_BEGIN_S: Final[float] = 3.6


def _fmt_seconds(value: float) -> str:
    """Format a seconds value for SMIL ``begin``/``dur`` (no trailing zeros)."""
    if value == int(value):
        return f"{int(value)}s"
    return f"{value:g}s"


def boot_animate(
    *,
    attribute: str,
    begin_s: float,
    dur_s: float,
    from_value: str | None = None,
    to_value: str | None = None,
    values: tuple[str, ...] | None = None,
    key_times: tuple[str, ...] | None = None,
) -> str:
    """Return one ``<animate>`` element with ``fill="freeze"``.

    Provide either ``from_value``+``to_value`` or ``values``. The element
    is self-closed so it can be embedded directly inside its target.
    """
    parts: list[str] = ["<animate", f'attributeName="{attribute}"']
    if values is not None:
        parts.append(f'values="{";".join(values)}"')
        if key_times is not None:
            parts.append(f'keyTimes="{";".join(key_times)}"')
    else:
        if from_value is None or to_value is None:
            msg = "Provide either 'values' or both 'from_value' and 'to_value'."
            raise ValueError(msg)
        parts.append(f'from="{from_value}"')
        parts.append(f'to="{to_value}"')
    parts.append(f'begin="{_fmt_seconds(begin_s)}"')
    parts.append(f'dur="{_fmt_seconds(dur_s)}"')
    parts.append('fill="freeze"')
    return " ".join(parts) + "/>"


def boot_transform(
    *,
    transform_type: str,
    from_value: str,
    to_value: str,
    begin_s: float,
    dur_s: float,
) -> str:
    """Return one ``<animateTransform>`` with ``additive="sum"`` and freeze.

    ``additive="sum"`` lets the animated transform compose with any
    static ``transform`` already on the parent group (e.g. a translate
    that places a bar at its row position).
    """
    return (
        "<animateTransform "
        'attributeName="transform" '
        f'type="{transform_type}" '
        f'from="{from_value}" '
        f'to="{to_value}" '
        f'begin="{_fmt_seconds(begin_s)}" '
        f'dur="{_fmt_seconds(dur_s)}" '
        'additive="sum" '
        'fill="freeze"/>'
    )


def idle_animate(
    *,
    attribute: str,
    values: tuple[str, ...],
    begin_s: float,
    dur_s: float,
    key_times: tuple[str, ...] | None = None,
) -> str:
    """Return one looping ``<animate>`` (``repeatCount="indefinite"``).

    Idle accents must return to the baseline at the end of each cycle so
    the dashboard always rests at the static design state between pulses.
    """
    parts: list[str] = [
        "<animate",
        f'attributeName="{attribute}"',
        f'values="{";".join(values)}"',
    ]
    if key_times is not None:
        parts.append(f'keyTimes="{";".join(key_times)}"')
    parts.append(f'begin="{_fmt_seconds(begin_s)}"')
    parts.append(f'dur="{_fmt_seconds(dur_s)}"')
    parts.append('repeatCount="indefinite"')
    return " ".join(parts) + "/>"
