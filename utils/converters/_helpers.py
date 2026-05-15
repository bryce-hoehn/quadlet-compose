"""Internal helper utilities for converter functions."""

from typing import Any


def _as_list(value: Any) -> list[str]:
    """Normalise a value to a list of strings.

    Handles ``None``, single strings, and lists.
    """
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    return [str(v) for v in value]


def _as_optional_list(value: Any) -> list[str] | None:
    """Like :func:`_as_list` but returns ``None`` when *value* is ``None``."""
    if value is None:
        return None
    return _as_list(value)
