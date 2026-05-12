"""Podlet workarounds — enabled by default.

Each hack is a self-contained module that transforms compose data to work
around podlet limitations.  All hacks are enabled by default.  Set
``PODLET_COMPOSE_HACKS=false`` to disable them all.

Available hacks:

- ``interpolate`` — resolve ``$VAR`` / ``${VAR}`` / ``${VAR:-default}``
  patterns from ``.env`` and environment
- ``name_inject`` — inject ``name:`` from parent directory if missing
- ``normalize`` — strip/fix fields podlet cannot handle
  (hostname, network_mode, unsupported depends_on conditions, etc.)
- ``expand`` — expand single-value devices, ports, and volumes
  to the ``host:container`` form podlet requires
- ``strip_extensions`` — remove ``x-*`` compose extension keys

Example::

    PODLET_COMPOSE_HACKS=false quadlet-compose up
"""

import importlib
import os
from pathlib import Path
from typing import Callable

# ---------------------------------------------------------------------------
# Shared helper
# ---------------------------------------------------------------------------


def _iter_services(data: dict):
    """Yield ``(name, service_dict)`` for each valid service entry."""
    services = data.get("services")
    if not services:
        return
    for name, svc in services.items():
        if isinstance(svc, dict):
            yield name, svc


# ---------------------------------------------------------------------------
# Hack registry
#
# TEXT_HACKS operate on raw YAML text before parsing.
# DICT_HACKS operate on the parsed YAML dict after loading.
# ---------------------------------------------------------------------------

TextHackFunc = Callable[[str, Path], str]
DictHackFunc = Callable[..., None]

TEXT_HACKS: dict[str, dict[str, object]] = {
    "interpolate": {
        "description": "Resolve $VAR / ${VAR} / ${VAR:-default} from .env and environment",
        "module": "hacks.interpolate",
        "func": "interpolate",
    },
}

DICT_HACKS: dict[str, dict[str, object]] = {
    "name_inject": {
        "description": "Inject name: from parent directory if missing",
        "module": "hacks.name_inject",
        "func": "name_inject",
        "needs_path": True,
    },
    "normalize": {
        "description": "Strip/fix fields podlet cannot handle",
        "module": "hacks.normalize",
        "func": "normalize_service_fields",
    },
    "expand": {
        "description": "Expand single-value devices, ports, and volumes",
        "module": "hacks.expand",
        "func": "expand_single_values",
    },
    "strip_extensions": {
        "description": "Remove x-* compose extension keys",
        "module": "hacks.strip_extensions",
        "func": "strip_extensions",
    },
}

ALL_HACKS = {**TEXT_HACKS, **DICT_HACKS}


def _hacks_enabled() -> bool:
    """Return whether hacks are enabled.

    Defaults to ``True``.  Set ``PODLET_COMPOSE_HACKS=false`` to disable.
    """
    raw = os.environ.get("PODLET_COMPOSE_HACKS", "").strip().lower()
    return raw not in ("false", "0", "no")


def _load_func(entry: dict) -> Callable:
    """Lazy-import a hack function from its registry entry."""
    mod = importlib.import_module(entry["module"])  # type: ignore[arg-type]
    return getattr(mod, entry["func"])  # type: ignore[arg-type]


def apply_text_hacks(raw_text: str, compose_path: Path) -> str:
    """Apply all text-level hacks to *raw_text*.

    Returns the (possibly modified) text.  No-ops when hacks are disabled.
    """
    if not _hacks_enabled():
        return raw_text
    for name, entry in TEXT_HACKS.items():
        func: TextHackFunc = _load_func(entry)
        raw_text = func(raw_text, compose_path)
    return raw_text


def apply_dict_hacks(data: dict, compose_path: Path) -> None:
    """Apply all dict-level hacks to *data* in-place.

    No-ops when hacks are disabled.
    """
    if not _hacks_enabled():
        return
    for name, entry in DICT_HACKS.items():
        func: DictHackFunc = _load_func(entry)
        if entry.get("needs_path"):
            func(data, compose_path)
        else:
            func(data)
