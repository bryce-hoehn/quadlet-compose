"""Compose file parsing and resolution."""

import os
import tempfile
from collections import defaultdict
from pathlib import Path
from string import Template

import yaml

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


def _load_dotenv(compose_path: Path) -> dict[str, str]:
    """Load variables from a .env file next to the compose file."""
    env_path = compose_path.parent.resolve() / ".env"
    if not env_path.is_file():
        return {}
    env = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            env[key.strip()] = value.strip().strip("\"'")
    return env


def _interpolate(text: str, variables: dict[str, str]) -> str:
    """Replace ``$VAR`` and ``${VAR}`` patterns using string.Template.

    Unresolved variables are replaced with empty strings, matching
    docker-compose behavior.  ``$$`` is treated as a literal ``$`` escape.
    """
    mapping = defaultdict(str, variables)
    return Template(text).substitute(mapping)


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

    Performs variable interpolation (``$VAR`` and ``${VAR}``) using values
    from the ``.env`` file next to the compose file and the process
    environment (env vars take precedence).  Unresolved variables are left
    as-is.  ``$$`` is treated as a literal ``$`` escape.

    Also ensures a top-level ``name`` field exists (required by ``--pod``),
    defaulting to the parent directory name.
    """
    raw = compose_path.read_text(encoding="utf-8")

    # Build variable table: .env values overridden by actual environment
    variables = {**_load_dotenv(compose_path), **os.environ}

    # Interpolate variables in the raw text
    resolved = _interpolate(raw, variables)

    data = yaml.safe_load(resolved) or {}

    # Inject name from parent directory if missing
    if not data.get("name"):
        data["name"] = compose_path.parent.resolve().name

    tmp = tempfile.NamedTemporaryFile(
        mode="w",
        suffix=compose_path.suffix,
        prefix="podlet-compose-",
        delete=False,
    )
    yaml.dump(data, tmp, default_flow_style=False, sort_keys=False)
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
    with open(compose_path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

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
