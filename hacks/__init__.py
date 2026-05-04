"""Podlet workarounds — all disabled by default.

Each hack is a self-contained module that transforms compose data to work
around podlet limitations.  Enable individual hacks via the
``PODLET_COMPOSE_HACKS`` environment variable (comma-separated list of
hack names, or ``all`` to enable every hack).

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

    PODLET_COMPOSE_HACKS=interpolate,name_inject podlet-compose up
    PODLET_COMPOSE_HACKS=all podlet-compose up
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


def _enabled_hacks() -> list[str]:
    """Return the list of hack names enabled via ``PODLET_COMPOSE_HACKS``."""
    raw = os.environ.get("PODLET_COMPOSE_HACKS", "").strip()
    if not raw:
        return []
    if raw.lower() == "all":
        return list(ALL_HACKS.keys())
    return [name.strip() for name in raw.split(",") if name.strip() in ALL_HACKS]


def _load_func(entry: dict) -> Callable:
    """Lazy-import a hack function from its registry entry."""
    mod = importlib.import_module(entry["module"])  # type: ignore[arg-type]
    return getattr(mod, entry["func"])  # type: ignore[arg-type]


def apply_text_hacks(raw_text: str, compose_path: Path) -> str:
    """Apply enabled text-level hacks to *raw_text*.

    Returns the (possibly modified) text.  No-ops when no text hacks are
    enabled.
    """
    enabled = _enabled_hacks()
    for name in enabled:
        if name in TEXT_HACKS:
            func: TextHackFunc = _load_func(TEXT_HACKS[name])
            raw_text = func(raw_text, compose_path)
    return raw_text


def apply_dict_hacks(data: dict, compose_path: Path) -> None:
    """Apply enabled dict-level hacks to *data* in-place.

    No-ops when no dict hacks are enabled.
    """
    enabled = _enabled_hacks()
    for name in enabled:
        if name in DICT_HACKS:
            entry = DICT_HACKS[name]
            func: DictHackFunc = _load_func(entry)
            if entry.get("needs_path"):
                func(data, compose_path)
            else:
                func(data)
