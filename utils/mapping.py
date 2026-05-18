"""
Compose-spec → Quadlet unit mapping layer
"""

from collections.abc import Sequence
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any, Callable, TypeVar
from pathlib import Path

from models.compose import (
    Network,
    Service,
    ServiceBuild,
    Volume,
)
from pydantic import BaseModel

from models.quadlet.build import BuildUnit
from models.quadlet.container import ContainerUnit
from models.quadlet.network import NetworkUnit
from models.quadlet.pod import PodUnit
from models.quadlet.volume import VolumeUnit

from .converters._helpers import _resolve_relative_path
from .field_maps import (
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
    field_map: Sequence[FieldMapEntry],
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

        # Unwrap Pydantic models to plain dicts for converter compatibility.
        # Converters expect primitive types (str, int, bool, list, dict),
        # but Pydantic-validated compose models yield BaseModel instances
        # for nested fields like healthcheck, logging, ipam, etc.
        if isinstance(value, BaseModel):
            value = value.model_dump(exclude_none=True)

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
    compose_path: Path | None = None,
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
        else:
            # No explicit image — use project-prefixed service name.
            # For build services this matches the BuildUnit.ImageTag.
            # Use localhost/ prefix for locally-built images so Podman
            # won't try to pull from a remote registry.
            raw = f"{project_name}-{service_name}" if project_name else service_name
            kwargs["Image"] = f"localhost/{raw}"

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
    compose_path: Path | None = None,
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

    # Set ImageTag if not provided — use localhost/ prefix for
    # locally-built images so Podman won't try a remote pull.
    if "ImageTag" not in kwargs:
        raw = f"{project_name}-{service_name}" if project_name else service_name
        kwargs["ImageTag"] = f"localhost/{raw}"

    return BuildUnit(**kwargs)


def map_network(
    network: Network,
    *,
    network_name: str,
    project_name: str | None = None,
    compose_path: Path | None = None,
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
    compose_path: Path | None = None,
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
# Helpers
# ---------------------------------------------------------------------------

_HASH_LABEL_KEY = "io.quadlet-compose.hash"


def _render_with_hash(
    unit: PodUnit | ContainerUnit | NetworkUnit | VolumeUnit | BuildUnit,
) -> str:
    """Render a quadlet unit with a content-hash label in its ``Label`` field.

    The SHA-256 digest is computed from the unit rendered **without**
    the hash label, then the label is appended to ``unit.Label`` and
    the unit is re-rendered.  Because the label is added to the model's
    ``Label`` field, :meth:`to_quadlet` places it in the correct INI
    section (e.g. ``[Container]``) rather than in ``[Install]``.

    The function is idempotent: any existing hash labels are stripped
    before computing the digest so repeated calls produce the same
    result.
    """
    # Strip any prior hash labels so the digest is stable.
    if unit.Label:
        unit.Label = [l for l in unit.Label if not l.startswith(_HASH_LABEL_KEY)]
    # Compute digest from content without the hash label.
    digest = sha256(unit.to_quadlet().encode()).hexdigest()
    hash_label = f"{_HASH_LABEL_KEY}={digest}"
    if unit.Label is None:
        unit.Label = [hash_label]
    else:
        unit.Label.append(hash_label)
    return unit.to_quadlet()


# ---------------------------------------------------------------------------
# QuadletBundle — orchestrator output
# ---------------------------------------------------------------------------


@dataclass
class QuadletBundle:
    """Aggregation of all quadlet units produced from a single compose file.

    Attributes:
        project_name: Resolved project name (from compose ``name:``, directory, or explicit).
        pod: The pod unit (one per compose project).
        containers: List of container units (one per service).
        networks: List of network units.
        volumes: List of volume units.
        builds: List of build units (for services with ``build:``).
    """

    project_name: str = ""
    pod: PodUnit | None = None
    containers: list[ContainerUnit] = field(default_factory=list)
    networks: list[NetworkUnit] = field(default_factory=list)
    volumes: list[VolumeUnit] = field(default_factory=list)
    builds: list[BuildUnit] = field(default_factory=list)
    #: Maps container systemd service name → compose ``restart`` value.
    restart_policies: dict[str, str] = field(default_factory=dict)

    def _tag(self, project_name: str) -> None:
        """Inject project-ownership labels into all units.

        Appends the project label to any existing labels rather than
        replacing them, so compose ``labels:`` are preserved.
        """
        label = f"io.quadlet-compose.project={project_name}"
        all_units: list[
            PodUnit | ContainerUnit | NetworkUnit | VolumeUnit | BuildUnit
        ] = []
        if self.pod is not None:
            all_units.append(self.pod)
        all_units.extend(self.containers)
        all_units.extend(self.networks)
        all_units.extend(self.volumes)
        all_units.extend(self.builds)
        for unit in all_units:
            if unit.Label is None:
                unit.Label = [label]
            else:
                unit.Label.append(label)

    def service_names(self) -> list[str]:
        """Return the systemd service names for all units in this bundle.

        The Podman Quadlet generator names systemd services after the
        **file stem** with a type suffix for non-container units:

        * ``{stem}.container`` → ``{stem}.service``
        * ``{stem}.pod``       → ``{stem}-pod.service``
        * ``{stem}.network``   → ``{stem}-network.service``
        * ``{stem}.volume``    → ``{stem}-volume.service``
        * ``{stem}.build``     → ``{stem}-build.service``

        This method derives names from the same filenames
        :meth:`to_quadlet_files` produces, so the two always agree.
        """
        # Mapping from quadlet extension to the suffix Quadlet appends
        # to the stem when generating the systemd service name.
        _SUFFIX: dict[str, str] = {
            ".container": "",
            ".pod": "-pod",
            ".network": "-network",
            ".volume": "-volume",
            ".build": "-build",
        }
        names: list[str] = []
        for filename in self.to_quadlet_files():
            stem, ext = filename.rsplit(".", 1)
            ext = f".{ext}"
            suffix = _SUFFIX.get(ext, "")
            names.append(f"{stem}{suffix}.service")
        return names

    def to_quadlet_files(self) -> dict[str, str]:
        """Render all units to their quadlet file contents.

        Each file includes a ``Label=io.quadlet-compose.hash=<sha256>``
        line for change detection by ``compose up``.

        Returns:
            Dict mapping ``filename`` → ``quadlet file content``.
        """
        files: dict[str, str] = {}
        if self.pod is not None:
            name = self.pod.PodName or "pod"
            files[f"{name}.pod"] = _render_with_hash(self.pod)
        for unit in self.containers:
            name = unit.ContainerName or "container"
            files[f"{name}.container"] = _render_with_hash(unit)
        for unit in self.networks:
            name = unit.NetworkName or "network"
            files[f"{name}.network"] = _render_with_hash(unit)
        for unit in self.volumes:
            name = unit.VolumeName or "volume"
            files[f"{name}.volume"] = _render_with_hash(unit)
        for unit in self.builds:
            tag = unit.ImageTag or "build"
            files[f"{tag}.build"] = _render_with_hash(unit)
        return files


def map_compose(
    compose_data: dict[str, Any],
    *,
    project_name: str | None = None,
    compose_path: Path | None = None,
) -> QuadletBundle:
    """Map a full compose specification dict to a ``QuadletBundle``.

    This is the top-level entry point for compose→quadlet translation.

    Args:
        compose_data: The parsed compose file as a dict (from YAML).
        project_name: Explicit project name (overrides compose ``name:`` and
            directory-based fallback).
        compose_path: Path to the compose file, used to derive the project
            name from the parent directory when neither *project_name* nor
            ``compose_data["name"]`` is set.

    Returns:
        A ``QuadletBundle`` containing all generated quadlet units.
    """
    bundle = QuadletBundle()

    # Determine project name
    if not project_name:
        project_name = compose_data.get("name") or (
            compose_path.parent.name if compose_path else "default"
        )

    bundle.project_name = project_name

    # Create pod for the project.
    # Quadlet appends ``-pod`` to the file stem
    # when generating the systemd service name (e.g. ``jellyfin.pod``
    # → ``jellyfin-pod.service``).

    pod_service_name = f"{project_name}.pod"
    bundle.pod = PodUnit(
        PodName=project_name,
        ExitPolicy="stop",
    )

    compose_dir = compose_path.parent if compose_path else Path.cwd()

    # Map services
    services = compose_data.get("services", {})
    if services:
        for svc_name, svc in services.items():
            svc_model = Service.model_validate(svc) if isinstance(svc, dict) else svc

            # Handle build config
            if svc_model.build:
                build_obj = svc_model.build
                if isinstance(build_obj, str):
                    build_obj = ServiceBuild.model_validate({"context": build_obj})
                build_unit = map_build(
                    build_obj,
                    service_name=svc_name,
                    project_name=project_name,
                )
                # Resolve relative build context against the compose file
                # directory.  Quadlet would otherwise resolve it against
                # ~/.config/containers/systemd/.
                if build_unit.SetWorkingDirectory:
                    build_unit.SetWorkingDirectory = _resolve_relative_path(
                        build_unit.SetWorkingDirectory,
                        compose_dir,
                    )
                bundle.builds.append(build_unit)

            # Map the service to a container
            container = map_service(
                svc_model,
                service_name=svc_name,
                project_name=project_name,
                pod_name=pod_service_name,
            )

            # Resolve relative bind-mount paths in volume sources against
            # the compose file directory.  Named volumes (bare names
            # without ``./`` or ``../`` prefixes) must NOT be resolved.
            if container.Volume:
                resolved: list[str] = []
                for vol in container.Volume:
                    parts = vol.split(":", 2)
                    src = parts[0]
                    if src.startswith("./") or src.startswith("../"):
                        parts[0] = _resolve_relative_path(src, compose_dir)
                    resolved.append(":".join(parts))
                container.Volume = resolved

            # Resolve relative paths in env_file sources against the
            # compose file directory.  Quadlet would otherwise resolve
            # them against ~/.config/containers/systemd/.
            if container.EnvironmentFile:
                container.EnvironmentFile = [
                    _resolve_relative_path(p, compose_dir)
                    for p in container.EnvironmentFile
                ]

            # Podman requires PublishPort on the *pod*, not individual
            # containers, when containers share a pod's network
            # namespace.
            if container.PublishPort and bundle.pod is not None:
                if bundle.pod.PublishPort is None:
                    bundle.pod.PublishPort = []
                seen = set(bundle.pod.PublishPort)
                for port in container.PublishPort:
                    if port not in seen:
                        seen.add(port)
                        bundle.pod.PublishPort.append(port)
                container.PublishPort = None

            # Podman does not allow setting UserNS on individual
            # containers when they join a pod with an infra container.
            # Move UserNS from the container to the pod instead.
            if container.UserNS and bundle.pod is not None:
                if bundle.pod.UserNS is None:
                    bundle.pod.UserNS = container.UserNS
                elif bundle.pod.UserNS != container.UserNS:
                    from utils import ComposeError

                    raise ComposeError(
                        f"Conflicting userns_mode: pod already has "
                        f"UserNS={bundle.pod.UserNS!r}, but service "
                        f"{svc_name!r} specifies {container.UserNS!r}"
                    )
                container.UserNS = None

            bundle.containers.append(container)

            # Track restart policy for compose_up to handle.
            # Key is the systemd service name, which matches the quadlet
            # filename stem: ``{ContainerName}.service``.
            if svc_model.restart:
                svc_name_systemd = (
                    container.ContainerName or f"{project_name}-{svc_name}"
                )
                bundle.restart_policies[f"{svc_name_systemd}.service"] = (
                    svc_model.restart
                )

            # Add [Install] section with WantedBy=default.target for containers with restart policies.
            if svc_model.restart in ("always", "unless-stopped"):
                container.install = {"WantedBy": "default.target"}

            # Override Quadlet's default ExecStopPost=podman rm so that
            # containers persist after stop/failure (matching docker-
            # compose behaviour).  An empty assignment clears all
            # previous ExecStopPost entries in the generated service.
            container.service = {"ExecStopPost": ""}

    # Map networks
    networks = compose_data.get("networks", {})
    if networks:
        for net_name, net in networks.items():
            if net is None:
                net = {}
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
    volumes = compose_data.get("volumes", {})
    if volumes:
        for vol_name, vol in volumes.items():
            if vol is None:
                vol = {}
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

    bundle._tag(project_name)

    return bundle
