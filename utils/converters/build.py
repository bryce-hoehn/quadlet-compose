"""Converter functions for compose ServiceBuild → Quadlet BuildUnit fields."""

from typing import Any

from ._helpers import _as_list


def convert_build_context(value: Any) -> dict[str, Any]:
    """Convert compose build ``context`` to ``SetWorkingDirectory``."""
    if value is None:
        return {}
    return {"SetWorkingDirectory": str(value)}


def convert_build_dockerfile(value: Any) -> dict[str, Any]:
    """Convert compose build ``dockerfile`` to ``File``."""
    if value is None:
        return {}
    return {"File": str(value)}


def convert_build_target(value: Any) -> dict[str, Any]:
    """Convert compose build ``target`` to ``Target``."""
    if value is None:
        return {}
    return {"Target": str(value)}


def convert_build_pull(value: Any) -> dict[str, Any]:
    """Convert compose build ``pull`` to ``Pull``."""
    if value is None or value is False:
        return {}
    return {"Pull": "true"}


def convert_build_network(value: Any) -> dict[str, Any]:
    """Convert compose build ``network`` to ``Network``."""
    if value is None:
        return {}
    return {"Network": str(value)}


def convert_build_secrets(value: Any) -> dict[str, Any]:
    """Convert compose build ``secrets`` to ``Secret`` lines."""
    if value is None:
        return {}
    return {"Secret": [str(v) for v in _as_list(value)]}


def convert_build_labels(value: Any) -> dict[str, Any]:
    """Convert compose build ``labels`` to ``Label`` lines."""
    if value is None:
        return {}
    if isinstance(value, dict):
        return {"Label": [f"{k}={v}" for k, v in value.items()]}
    if isinstance(value, list):
        return {"Label": [str(v) for v in value]}
    return {}
