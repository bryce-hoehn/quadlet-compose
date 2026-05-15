"""Converter functions for compose Network → Quadlet NetworkUnit fields."""

from typing import Any


def convert_network_name(value: Any) -> dict[str, Any]:
    """Convert compose network ``name`` to ``NetworkName``."""
    if value is None:
        return {}
    return {"NetworkName": str(value)}


def convert_network_driver_opts(value: Any) -> dict[str, Any]:
    """Convert compose network ``driver_opts`` to ``Options`` lines."""
    if value is None:
        return {}
    if isinstance(value, dict):
        return {"Options": [f"{k}={v}" for k, v in value.items()]}
    return {}


def convert_network_internal(value: Any) -> dict[str, Any]:
    """Convert compose network ``internal`` to ``Internal``."""
    if value is None or value is False:
        return {}
    return {"Internal": "true"}


def convert_network_enable_ipv6(value: Any) -> dict[str, Any]:
    """Convert compose network ``enable_ipv6`` to ``IPv6``."""
    if value is None or value is False:
        return {}
    return {"IPv6": "true"}


def convert_network_labels(value: Any) -> dict[str, Any]:
    """Convert compose network ``labels`` to ``Label`` lines."""
    if value is None:
        return {}
    if isinstance(value, dict):
        return {"Label": [f"{k}={v}" for k, v in value.items()]}
    if isinstance(value, list):
        return {"Label": [str(v) for v in value]}
    return {}


def convert_network_ipam(value: Any) -> dict[str, Any]:
    """Convert compose network ``ipam`` config to quadlet fields.

    Handles ``ipam.driver`` → ``IPAMDriver`` and ``ipam.config`` →
    ``Subnet`` / ``Gateway`` lists.
    """
    if value is None:
        return {}
    result: dict[str, Any] = {}
    if isinstance(value, dict):
        driver = value.get("driver")
        if driver:
            result["IPAMDriver"] = str(driver)
        configs = value.get("config")
        if configs and isinstance(configs, list):
            for cfg in configs:
                if isinstance(cfg, dict):
                    subnet = cfg.get("subnet")
                    if subnet:
                        result.setdefault("Subnet", []).append(str(subnet))
                    gateway = cfg.get("gateway")
                    if gateway:
                        result.setdefault("Gateway", []).append(str(gateway))
    return result
