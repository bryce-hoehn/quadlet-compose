"""Internal helper utilities for converter functions."""

from pathlib import Path
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


def _resolve_relative_path(path: str, base_dir: Path) -> str:
    """Resolve a relative path against *base_dir* if it starts with ``./`` or ``../``.

    Absolute paths and non-path values are returned unchanged.
    """
    if path.startswith("./") or path.startswith("../"):
        return str((base_dir / path).resolve())
    return path


def _quote_env_if_needed(s: str) -> str:
    """Quote a ``KEY=VALUE`` string for systemd ``Environment=`` if needed.

    Systemd splits unquoted values on whitespace.  When the value
    portion contains spaces or tabs, the entire assignment is wrapped
    in double quotes so that systemd preserves the value verbatim.
    """
    if "=" not in s:
        return s
    _key, _, value = s.partition("=")
    if value and any(c in value for c in (" ", "\t")):
        escaped = value.replace('"', '\\"')
        return f'{_key}="{escaped}"'
    return s
