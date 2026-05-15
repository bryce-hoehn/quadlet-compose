"""Converters for compose fields that accept list-or-dict formats.

The auto-generated Pydantic models (from compose-spec.json) represent
``ListOrDict`` as either ``dict`` or ``set[str]`` (not ``list[str]``),
so every converter here must handle ``set`` in addition to ``list`` and
``dict``.
"""

from typing import Any


def _normalize_to_list(value: set[str] | list[str]) -> list[str]:
    """Normalize a set or list to a list.

    Sets are sorted for deterministic output; lists preserve order.
    """
    if isinstance(value, set):
        return sorted(str(v) for v in value)
    return [str(v) for v in value]


def convert_list_or_dict_to_env(value: Any) -> dict[str, Any]:
    """Convert compose ``environment`` (list or dict) to ``Environment`` lines.

    ``Environment=KEY=VALUE`` for quadlet container units.
    """
    if value is None:
        return {}
    if isinstance(value, dict):
        return {"Environment": [f"{k}={v}" for k, v in value.items() if v is not None]}
    if isinstance(value, (list, set)):
        return {"Environment": _normalize_to_list(value)}
    return {}


def convert_list_or_dict_to_labels(value: Any) -> dict[str, Any]:
    """Convert compose ``labels`` (list or dict) to ``Label`` lines."""
    if value is None:
        return {}
    if isinstance(value, dict):
        return {"Label": [f"{k}={v}" for k, v in value.items()]}
    if isinstance(value, (list, set)):
        return {"Label": _normalize_to_list(value)}
    return {}


def convert_list_or_dict_to_sysctls(value: Any) -> dict[str, Any]:
    """Convert compose ``sysctls`` (list or dict) to ``Sysctl`` lines."""
    if value is None:
        return {}
    if isinstance(value, dict):
        return {"Sysctl": [f"{k}={v}" for k, v in value.items()]}
    if isinstance(value, (list, set)):
        return {"Sysctl": _normalize_to_list(value)}
    return {}


def convert_list_or_dict_to_build_env(value: Any) -> dict[str, Any]:
    """Convert compose build ``args`` (list or dict) to ``Environment`` lines."""
    return convert_list_or_dict_to_env(value)


def convert_list_or_dict_to_build_labels(value: Any) -> dict[str, Any]:
    """Convert compose build ``labels`` (list or dict) to ``Label`` lines."""
    return convert_list_or_dict_to_labels(value)
