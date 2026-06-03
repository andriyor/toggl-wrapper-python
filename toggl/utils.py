"""Pure helpers shared across the app — no Qt, no I/O."""

from __future__ import annotations

from datetime import datetime, timezone


def is_dark(hex_color: str | None) -> bool:
    """Whether ``#rrggbb`` is dark enough to warrant light text."""
    if not hex_color:
        return False
    h = hex_color.lstrip("#")
    if len(h) != 6:
        return False
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255 < 0.6


def format_seconds(total: float) -> str:
    """Format a non-negative duration as ``HH:MM:SS``."""
    total = max(0, int(total))
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def parse_start(value: str | None) -> datetime | None:
    """Parse a Toggl ISO-8601 start timestamp into an aware UTC datetime."""
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt
