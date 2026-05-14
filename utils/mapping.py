"""Compose-spec → Quadlet unit mapping layer (thin orchestrator).

This module wires together the declarative field maps and converter
functions, then orchestrates the compose→quadlet translation via
:meth:`map_compose`.

Field maps live in :mod:`field_maps/`; converter functions live in
:mod:`converters`.

BUG FIX vs. previous version:
  - Pod name mismatch: the pod unit's ``PodName`` and the container's
    ``Pod`` reference are now both ``{project_name}-pod`` (previously
    the pod unit used bare ``project_name``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from compose_spec.models import (
    Network,
    Service,
    ServiceBuild,
    Volume,
)
from pydantic import BaseModel
from typing import TypeVar

from models.quadlet.build import BuildUnit
from models.quadlet.container import ContainerUnit
from models.quadlet.network import NetworkUnit
from models.quadlet.pod import PodUnit
from models.quadlet.volume import VolumeUnit

from field_maps import (
    BUILD_FIELD_MAP,
    NETWORK_FIELD_MAP,
    SERVICE_FIELD_MAP,
    VOLUME_FIELD_MAP,
)

# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

#: A converter maps a raw compose value to a dict of {quadlet_field: value}.
Converter = Callable[[Any], dict[str, Any]]

#: A field-map entry: (compose_attr, quadlet_attr, converter | None)
FieldMapEntry = tuple[str, str, Converter | None]

T = TypeVar("T", bound=BaseModel)

# ---------------------------------------------------------------------------
# Generic mapper
# ---------------------------------------------------------------------------


def _apply_field_map(
    source: BaseModel,
    field_map: list[FieldMapEntry],
) -> dict[str, Any]:
    """Apply a field map to a source model and return a flat dict of quadlet kwargs.

    For each entry in the field map:
    - Get the compose attribute value from the source model
    - If the value is None, skip
    - If a converter is provided, call it to get {quadlet_field: value}
    - Otherwise, use the quadlet_attr directly with the raw value
    """
    result: dict[str, Any] = {}
    for compose_attr, quadlet_attr, converter in field_map:
        value = getattr(source, compose_attr, None)
        if value is None:
            continue

        if converter is not None:
            converted = converter(value)
            if converted:
                result.update(converted)
        elif quadlet_attr:
            # 1:1 identity rename
            result[quadlet_attr] = value
    return result


# ---------------------------------------------------------------------------
# Public mapping functions
# ---------------------------------------------------------------------------


def map_service(
    service: Service,
    *,
    service_name: str,
    project_name: str | None = None,
    pod_name: str | None = None,
) -> ContainerUnit:
    """Map a compose ``Service`` to a quadlet ``ContainerUnit``.

    Args:
        service: The compose service model.
        service_name: The service key name from compose file.
        project_name: Optional project name for container naming.
        pod_name: Optional pod name to assign the container to.

    Returns:
        A ``ContainerUnit`` populated from the compose service.
    """
    kwargs = _apply_field_map(service, SERVICE_FIELD_MAP)

    # Set Image if not already set (required field)
    if "Image" not in kwargs:
        if service.image:
            kwargs["Image"] = service.image
        elif not service.build:
            # No image and no build — this is an error in compose
            kwargs["Image"] = service_name

    # Assign to pod if provided
    if pod_name:
        kwargs["Pod"] = pod_name

    # Set container name: explicit > project-prefixed > service name
    if "ContainerName" not in kwargs:
        if project_name:
            kwargs["ContainerName"] = f"{project_name}-{service_name}"
        else:
            kwargs["ContainerName"] = service_name

    return ContainerUnit(**kwargs)


def map_build(
    build: ServiceBuild,
    *,
    service_name: str,
    project_name: str | None = None,
) -> BuildUnit:
    """Map a compose ``ServiceBuild`` to a quadlet ``BuildUnit``.

    Args:
        build: The compose build model.
        service_name: The service key name (used for default ImageTag).
        project_name: Optional project name for image tagging.

    Returns:
        A ``BuildUnit`` populated from the compose build config.
    """
    kwargs = _apply_field_map(build, BUILD_FIELD_MAP)

    # Set ImageTag if not provided
    if "ImageTag" not in kwargs:
        tag = f"{project_name}-{service_name}" if project_name else service_name
        kwargs["ImageTag"] = tag

    return BuildUnit(**kwargs)


def map_network(
    network: Network,
    *,
    network_name: str,
    project_name: str | None = None,
) -> NetworkUnit:
    """Map a compose ``Network`` to a quadlet ``NetworkUnit``.

    Args:
        network: The compose network model.
        network_name: The network key name from compose file.
        project_name: Optional project name for network naming.

    Returns:
        A ``NetworkUnit`` populated from the compose network.
    """
    kwargs = _apply_field_map(network, NETWORK_FIELD_MAP)

    # Set NetworkName if not provided
    if "NetworkName" not in kwargs:
        if project_name:
            kwargs["NetworkName"] = f"{project_name}-{network_name}"
        else:
            kwargs["NetworkName"] = network_name

    return NetworkUnit(**kwargs)


def map_volume(
    volume: Volume,
    *,
    volume_name: str,
    project_name: str | None = None,
) -> VolumeUnit:
    """Map a compose ``Volume`` to a quadlet ``VolumeUnit``.

    Args:
        volume: The compose volume model.
        volume_name: The volume key name from compose file.
        project_name: Optional project name for volume naming.

    Returns:
        A ``VolumeUnit`` populated from the compose volume.
    """
    kwargs = _apply_field_map(volume, VOLUME_FIELD_MAP)

    # Set VolumeName if not provided
    if "VolumeName" not in kwargs:
        if project_name:
            kwargs["VolumeName"] = f"{project_name}-{volume_name}"
        else:
            kwargs["VolumeName"] = volume_name

    return VolumeUnit(**kwargs)


# ---------------------------------------------------------------------------
# QuadletBundle — orchestrator output
# ---------------------------------------------------------------------------


@dataclass
class QuadletBundle:
    """Aggregation of all quadlet units produced from a single compose file.

    Attributes:
        pod: The pod unit (one per compose project).
        containers: List of container units (one per service).
        networks: List of network units.
        volumes: List of volume units.
        builds: List of build units (for services with ``build:``).
    """

    pod: PodUnit | None = None
    containers: list[ContainerUnit] = field(default_factory=list)
    networks: list[NetworkUnit] = field(default_factory=list)
    volumes: list[VolumeUnit] = field(default_factory=list)
    builds: list[BuildUnit] = field(default_factory=list)

    def to_quadlet_files(self) -> dict[str, str]:
        """Render all units to their quadlet file contents.

        Returns:
            Dict mapping ``filename`` → ``quadlet file content``.
        """
        files: dict[str, str] = {}
        if self.pod is not None:
            name = self.pod.PodName or "pod"
            files[f"{name}.pod"] = self.pod.to_quadlet()
        for unit in self.containers:
            name = unit.ContainerName or "container"
            files[f"{name}.container"] = unit.to_quadlet()
        for unit in self.networks:
            name = unit.NetworkName or "network"
            files[f"{name}.network"] = unit.to_quadlet()
        for unit in self.volumes:
            name = unit.VolumeName or "volume"
            files[f"{name}.volume"] = unit.to_quadlet()
        for unit in self.builds:
            tag = unit.ImageTag or "build"
            files[f"{tag}.build"] = unit.to_quadlet()
        return files


def map_compose(
    compose_data: dict[str, Any],
    *,
    project_name: str | None = None,
) -> QuadletBundle:
    """Map a full compose specification dict to a ``QuadletBundle``.

    This is the top-level entry point for compose→quadlet translation.

    Args:
        compose_data: The parsed compose file as a dict (from YAML).
        project_name: Optional project name (defaults to directory name).

    Returns:
        A ``QuadletBundle`` containing all generated quadlet units.
    """
    from compose_spec.models import ComposeSpecification

    spec = ComposeSpecification.model_validate(compose_data)
    bundle = QuadletBundle()

    # Determine project name
    if not project_name:
        project_name = spec.name if spec.name else "default"

    # Create pod for the project — PodName matches the Pod= reference
    pod_name = f"{project_name}-pod"
    bundle.pod = PodUnit(
        PodName=pod_name,
        ExitPolicy="stop",
    )

    # Map services
    if spec.services:
        for svc_name, svc in spec.services.items():
            svc_model = Service.model_validate(svc) if isinstance(svc, dict) else svc

            # Handle build config
            if svc_model.build:
                build_obj = svc_model.build
                if isinstance(build_obj, str):
                    build_obj = ServiceBuild(context=build_obj)
                build_unit = map_build(
                    build_obj,
                    service_name=svc_name,
                    project_name=project_name,
                )
                bundle.builds.append(build_unit)

            # Map the service to a container
            container = map_service(
                svc_model,
                service_name=svc_name,
                project_name=project_name,
                pod_name=pod_name,
            )
            bundle.containers.append(container)

    # Map networks
    if spec.networks:
        for net_name, net in spec.networks.items():
            net_model = Network.model_validate(net) if isinstance(net, dict) else net
            # Skip external networks
            if net_model.external:
                continue
            network_unit = map_network(
                net_model,
                network_name=net_name,
                project_name=project_name,
            )
            bundle.networks.append(network_unit)

    # Map volumes
    if spec.volumes:
        for vol_name, vol in spec.volumes.items():
            vol_model = Volume.model_validate(vol) if isinstance(vol, dict) else vol
            # Skip external volumes
            if vol_model.external:
                continue
            volume_unit = map_volume(
                vol_model,
                volume_name=vol_name,
                project_name=project_name,
            )
            bundle.volumes.append(volume_unit)

    return bundle
