"""Compose file parsing and resolution."""

import tempfile
from pathlib import Path

from ruamel.yaml import YAML

from hacks import apply_text_hacks, apply_dict_hacks
from .config import get_unit_directory
from .utils import ComposeError

# Compose file search order (matches podlet's behavior)
COMPOSE_FILE_NAMES = [
    "compose.yaml",
    "compose.yml",
    "docker-compose.yaml",
    "docker-compose.yml",
    "podman-compose.yaml",
    "podman-compose.yml",
]


def resolve_compose_path(compose_file: str | None) -> Path:
    """Resolve the compose file path.

    If compose_file is None, searches the CWD following podlet's search order.
    Raises FileNotFoundError if no compose file is found.
    """
    if compose_file:
        p = Path(compose_file)
        if not p.is_file():
            raise ComposeError(f"Compose file not found: {p}")
        return p

    for name in COMPOSE_FILE_NAMES:
        candidate = Path.cwd() / name
        if candidate.is_file():
            return candidate
    raise ComposeError("No compose file found in current directory.")


def prepare_compose(compose_path: Path) -> Path:
    """Prepare a compose file for use with ``podlet compose``.

    Reads the compose file, applies any enabled hacks (text-level then
    dict-level), and writes the result to a temporary file.  All hacks
    are **enabled by default**; set ``PODLET_COMPOSE_HACKS=false`` to
    disable them.

    See the ``hacks/`` package for available hacks.

    Note: ``build:`` is now handled natively by podlet v0.3.1+ which
    generates ``.build`` Quadlet files.  No pre-build step is needed.
    """
    raw = compose_path.read_text(encoding="utf-8")

    # Apply text-level hacks (e.g. variable interpolation)
    raw = apply_text_hacks(raw, compose_path)

    # Parse with ruamel.yaml for round-trip preservation
    ryaml = YAML()
    data = ryaml.load(raw)
    if data is None:
        data = {}

    # Apply dict-level hacks (e.g. normalize, expand, name injection)
    apply_dict_hacks(data, compose_path)

    # Write to temp file
    tmp = tempfile.NamedTemporaryFile(
        mode="w",
        suffix=compose_path.suffix,
        prefix="podlet-compose-",
        delete=False,
    )
    ryaml.dump(data, tmp)
    tmp.close()
    return Path(tmp.name)


def parse_compose(compose_path: Path) -> dict:
    """Parse a compose file and return the full data plus derived metadata.

    Returns a dict with:
        - project: str — project name (from `name:` field or directory name)
        - services: dict — full service configs
        - volumes: dict — full volume configs
        - networks: dict — full network configs
        - service_names: list[str] — service name keys
        - volume_names: list[str] — volume name keys
        - network_names: list[str] — network name keys
    """
    ryaml = YAML()
    with open(compose_path, encoding="utf-8") as f:
        data = ryaml.load(f) or {}

    project = data.get("name") or compose_path.parent.resolve().name
    services = data.get("services") or {}
    volumes = data.get("volumes") or {}
    networks = data.get("networks") or {}

    return {
        "project": project,
        "services": services,
        "volumes": volumes,
        "networks": networks,
        "service_names": list(services.keys()),
        "volume_names": list(volumes.keys()),
        "network_names": list(networks.keys()),
    }


def get_image_services(compose_data: dict) -> dict:
    """Extract services with images from pre-parsed compose data."""
    services = compose_data["services"]
    return {
        name: config["image"]
        for name, config in services.items()
        if isinstance(config, dict) and "image" in config
    }


def get_build_services(compose_data: dict) -> dict:
    """Extract services with build contexts from pre-parsed compose data."""
    services = compose_data["services"]
    build_services = {}
    for name, config in services.items():
        if isinstance(config, dict) and "build" in config:
            build_info = config["build"]
            if isinstance(build_info, str):
                build_services[name] = {"context": build_info}
            elif isinstance(build_info, dict):
                build_services[name] = build_info
    return build_services


def get_service_targets(compose_data: dict) -> list[str]:
    """Determine systemd service targets based on existing quadlet files.

    Checks for .pod or .kube files in the unit directory to determine mode:
    - Pod mode: returns [f"{project}-pod"] if .pod file exists
    - Kube mode: returns [project] if .kube file exists
    - Plain mode: returns individual service names

    Used by lifecycle commands (start, stop, restart) to target the
    appropriate systemd service(s).
    """
    project = compose_data["project"]
    unit_dir = get_unit_directory()

    if (unit_dir / f"{project}.pod").exists():
        return [f"{project}-pod"]

    if (unit_dir / f"{project}.kube").exists():
        return [project]

    return compose_data["service_names"]
