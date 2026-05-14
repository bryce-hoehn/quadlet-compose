"""Duration parsing for compose time specifications."""

import re


def _parse_duration_seconds(value: str | int | float) -> int:
    """Parse a compose duration string to total seconds.

    Supports:
    - Plain numbers (treated as seconds)
    - Go-style duration strings: ``1h30m10s``, ``90m``, ``3600s``

    BUG FIX: Previous version multiplied by 1e9 (nanoseconds).
    Now correctly treats plain numbers as seconds.
    """
    if isinstance(value, (int, float)):
        return int(value)

    text = str(value).strip()
    if not text:
        return 0

    # Try plain number first
    try:
        return int(float(text))
    except ValueError:
        pass

    # Parse Go-style duration
    total = 0
    for match in re.finditer(r"(\d+)([hms])", text):
        amount = int(match.group(1))
        unit = match.group(2)
        if unit == "h":
            total += amount * 3600
        elif unit == "m":
            total += amount * 60
        elif unit == "s":
            total += amount
    return total
