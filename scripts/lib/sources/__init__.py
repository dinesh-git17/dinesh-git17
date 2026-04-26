"""Per-source data fetchers for the live dashboard.

Each module in this package exposes a single ``fetch(...)`` entry point
that returns a typed dataclass result. Source modules do not read or
write the SVG; they are pure functions over their inputs.
"""
