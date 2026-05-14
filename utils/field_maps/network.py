"""Network → NetworkUnit field mapping table."""

from __future__ import annotations

from converters import (
    convert_network_driver_opts,
    convert_network_enable_ipv6,
    convert_network_internal,
    convert_network_ipam,
    convert_network_labels,
    convert_network_name,
)

NETWORK_FIELD_MAP = [
    ("name", "NetworkName", convert_network_name),
    ("driver", "Driver", lambda v: {"Driver": str(v)} if v else {}),
    ("driver_opts", "Options", convert_network_driver_opts),
    ("ipam", "", convert_network_ipam),
    ("internal", "Internal", convert_network_internal),
    ("enable_ipv6", "IPv6", convert_network_enable_ipv6),
    ("labels", "Label", convert_network_labels),
]
