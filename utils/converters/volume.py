"""Converter functions for compose Volume → Quadlet VolumeUnit fields."""

from __future__ import annotations

from typing import Any


def convert_volume_name(value: Any) -> dict[str, Any]:
    """Convert compose volume ``name`` to ``VolumeName``."""
    if value is None:
        return {}
    return {"VolumeName": str(value)}


def convert_volume_labels(value: Any) -> dict[str, Any]:
    """Convert compose volume ``labels`` to ``Label`` lines."""
    if value is None:
        return {}
    if isinstance(value, dict):
        return {"Label": [f"{k}={v}" for k, v in value.items()]}
    if isinstance(value, list):
        return {"Label": [str(v) for v in value]}
    return {}
