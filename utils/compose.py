from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml
from models.compose import ComposeSpecification

# Compose file search order (matches podman-compose behavior)
COMPOSE_FILE_NAMES = [
    "compose.yaml",
    "compose.yml",
    "docker-compose.yaml",
    "docker-compose.yml",
    "podman-compose.yaml",
    "podman-compose.yml",
]


class ComposeError(Exception):
    """Error raised for compose file issues."""


def resolve_compose_path(compose_file: str | None) -> Path:
    """Resolve the compose file path.

    If compose_file is None, searches the CWD following standard search order.
    Raises FileNotFoundError if no compose file is found.
    """
    if compose_file:
        p = Path(compose_file)
        if not p.is_file():
            raise FileNotFoundError(f"Compose file not found: {p}")
        return p

    for name in COMPOSE_FILE_NAMES:
        candidate = Path.cwd() / name
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("No compose file found in current directory.")


def parse_compose(compose_path: Path) -> dict:
    """Parse a compose file using PyYAML and validate with Pydantic models.

    Returns the raw dict (validated) for use by the mapping layer.
    """
    with open(compose_path) as f:
        data = yaml.safe_load(f)

    if data is None:
        raise ComposeError(f"Compose file is empty: {compose_path}")

    # Validate against compose-spec Pydantic models
    ComposeSpecification.model_validate(data)

    return data


def resolve_project_name(
    compose_data: dict,
    compose_path: Path | None = None,
) -> str:
    """Resolve the project name from compose data.

    Uses ``name:`` from the compose file, falls back to the parent directory
    name of *compose_path*, or ``"default"``.
    """
    return compose_data.get("name") or (
        compose_path.parent.name if compose_path else "default"
    )


@dataclass
class ServiceInfo:
    """Lightweight service metadata — avoids the full ``map_compose`` pipeline.

    Attributes:
        project_name: Resolved project name.
        container_names: Mapping of ``service_name`` → ``container_name``
            (project-prefixed unless explicitly set via ``container_name:``).
        service_names: Ordered list of service keys from the compose file.
        images: Mapping of ``service_name`` → image reference (``None`` if
            the service uses ``build:`` without an explicit ``image:``).
    """

    project_name: str = ""
    container_names: dict[str, str] = field(default_factory=dict)
    service_names: list[str] = field(default_factory=list)
    images: dict[str, str | None] = field(default_factory=dict)


def get_service_info(
    compose_data: dict,
    compose_path: Path | None = None,
) -> ServiceInfo:
    """Extract lightweight service info from parsed compose data.

    This is a cheaper alternative to ``map_compose()`` for commands that
    only need the project name and container names (e.g. ``top``, ``logs``,
    ``ps``, ``kill``, ``images``).  It skips the full field-map pipeline,
    quadlet model construction, and label injection.
    """
    project_name = resolve_project_name(compose_data, compose_path)

    services = compose_data.get("services") or {}
    container_names: dict[str, str] = {}
    images: dict[str, str | None] = {}

    for svc_name, svc_config in services.items():
        if svc_config is None:
            svc_config = {}

        # Container name: explicit container_name > project-prefixed > service name
        explicit = svc_config.get("container_name")
        if explicit:
            container_names[svc_name] = explicit
        else:
            container_names[svc_name] = (
                f"{project_name}-{svc_name}" if project_name else svc_name
            )

        # Image: explicit image or None (build-only)
        images[svc_name] = svc_config.get("image")

    return ServiceInfo(
        project_name=project_name,
        container_names=container_names,
        service_names=list(services.keys()),
        images=images,
    )
