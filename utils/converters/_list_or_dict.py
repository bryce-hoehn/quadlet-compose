"""Converters for compose fields that accept list-or-dict formats."""

from typing import Any


def convert_list_or_dict_to_env(value: Any) -> dict[str, Any]:
    """Convert compose ``environment`` (list or dict) to ``Environment`` lines.

    ``Environment=KEY=VALUE`` for quadlet container units.
    """
    if value is None:
        return {}
    if isinstance(value, dict):
        return {"Environment": [f"{k}={v}" for k, v in value.items() if v is not None]}
    if isinstance(value, list):
        return {"Environment": [str(v) for v in value]}
    return {}


def convert_list_or_dict_to_labels(value: Any) -> dict[str, Any]:
    """Convert compose ``labels`` (list or dict) to ``Label`` lines."""
    if value is None:
        return {}
    if isinstance(value, dict):
        return {"Label": [f"{k}={v}" for k, v in value.items()]}
    if isinstance(value, list):
        return {"Label": [str(v) for v in value]}
    return {}


def convert_list_or_dict_to_sysctls(value: Any) -> dict[str, Any]:
    """Convert compose ``sysctls`` (list or dict) to ``Sysctl`` lines."""
    if value is None:
        return {}
    if isinstance(value, dict):
        return {"Sysctl": [f"{k}={v}" for k, v in value.items()]}
    if isinstance(value, list):
        return {"Sysctl": [str(v) for v in value]}
    return {}


def convert_list_or_dict_to_build_env(value: Any) -> dict[str, Any]:
    """Convert compose build ``args`` (list or dict) to ``Environment`` lines."""
    return convert_list_or_dict_to_env(value)


def convert_list_or_dict_to_build_labels(value: Any) -> dict[str, Any]:
    """Convert compose build ``labels`` (list or dict) to ``Label`` lines."""
    return convert_list_or_dict_to_labels(value)
