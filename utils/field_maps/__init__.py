"""Declarative field-map tables for compose→quadlet translation.

Each module exports a ``FIELD_MAP`` list of ``(compose_attr, quadlet_attr, converter | None)``
tuples consumed by :func:`utils.mapping._apply_field_map`.
"""

from field_maps.service import SERVICE_FIELD_MAP
from field_maps.build import BUILD_FIELD_MAP
from field_maps.network import NETWORK_FIELD_MAP
from field_maps.volume import VOLUME_FIELD_MAP

__all__ = [
    "SERVICE_FIELD_MAP",
    "BUILD_FIELD_MAP",
    "NETWORK_FIELD_MAP",
    "VOLUME_FIELD_MAP",
]
