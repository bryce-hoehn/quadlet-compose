"""Compose file parsing and resolution."""

import os
import tempfile
from collections import defaultdict
from pathlib import Path
from string import Template

import yaml
from ruamel.yaml import YAML

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


# ---------------------------------------------------------------------------
# Podlet workarounds — applied via ruamel.yaml for round-trip preservation
# ---------------------------------------------------------------------------


def _strip_image_tags_with_digests(data: dict) -> None:
    """Strip image tags when a digest is also present.

    Podlet rejects ``image: foo:v1@sha256:abc``.  This converts it to
    ``image: foo@sha256:abc`` (keep digest, drop tag).
    """
    services = data.get("services")
    if not services:
        return
    for svc in services.values():
        if not isinstance(svc, dict):
            continue
        image = svc.get("image")
        if isinstance(image, str) and "@" in image and ":" in image.split("@")[0]:
            # image has both tag and digest: strip the tag
            name_digest = image.split(":")
            # Rejoin everything except the tag before @
            # e.g. "ghcr.io/immich/immich:v1.2.3@sha256:abc" → "ghcr.io/immich/immich@sha256:abc"
            at_idx = image.index("@")
            last_colon_before_at = image.rfind(":", 0, at_idx)
            if last_colon_before_at > 0:
                svc["image"] = image[:last_colon_before_at] + image[at_idx:]


def _expand_single_values(data: dict) -> None:
    """Auto-expand single-value entries in devices, ports, and volumes.

    Docker-compose allows short forms like ``devices: ["/dev/dri"]`` or
    ``ports: ["8080"]``.  Podlet requires the full ``host:container`` form.
    This expands:
    - ``devices: ["/dev/dri"]`` → ``devices: ["/dev/dri:/dev/dri"]``
    - ``ports: ["8080"]`` → ``ports: ["8080:8080"]``
    - ``volumes: ["./config"]`` → ``volumes: ["./config:/config"]`` (path-like)
    Named volumes (no ``/`` or ``.`` prefix) are left as-is.
    """
    services = data.get("services")
    if not services:
        return
    for svc in services.values():
        if not isinstance(svc, dict):
            continue

        # Expand devices
        _expand_list(svc, "devices", colon_expand=True)

        # Expand ports
        _expand_list(svc, "ports", colon_expand=True)

        # Expand volumes (only path-like single values)
        vols = svc.get("volumes")
        if isinstance(vols, list):
            new_vols = []
            for vol in vols:
                if isinstance(vol, str) and ":" not in vol:
                    # Named volumes have no / or . prefix — leave them alone
                    if "/" in vol or vol.startswith("."):
                        new_vols.append(f"{vol}:{vol}")
                    else:
                        new_vols.append(vol)
                else:
                    new_vols.append(vol)
            svc["volumes"] = new_vols


def _expand_list(svc: dict, key: str, *, colon_expand: bool) -> None:
    """Expand single-value entries in a service list by duplicating the value."""
    items = svc.get(key)
    if not isinstance(items, list):
        return
    new_items = []
    for item in items:
        if isinstance(item, str) and ":" not in item:
            new_items.append(f"{item}:{item}")
        else:
            new_items.append(item)
    svc[key] = new_items


def _strip_extensions(data: dict) -> None:
    """Remove all top-level ``x-*`` extension keys from the compose data.

    Podlet does not support compose extensions (e.g. ``x-custom``, ``x-env``).
    """
    keys_to_remove = [k for k in data if isinstance(k, str) and k.startswith("x-")]
    for k in keys_to_remove:
        del data[k]


def _inject_build_tags(data: dict) -> None:
    """Inject a default image tag for services with ``build:`` but no ``image:``.

    Podlet requires an image tag when converting ``build:`` to a quadlet
    ``.build`` file.  This adds ``image: {service_name}:latest`` when missing.
    """
    services = data.get("services")
    if not services:
        return
    for svc_name, svc in services.items():
        if not isinstance(svc, dict):
            continue
        if "build" in svc and "image" not in svc:
            svc["image"] = f"{svc_name}:latest"


# ---------------------------------------------------------------------------


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

    Applies the following transformations (all via ruamel.yaml round-trip):

    1. Variable interpolation (``$VAR`` / ``${VAR}``) from ``.env`` and
       environment — unresolved vars become empty strings.
    2. Strip image tags when a digest is also present.
    3. Auto-expand single-value devices, ports, and path-like volumes.
    4. Remove ``x-*`` compose extension keys.
    5. Inject ``image:`` for services with ``build:`` but no image tag.
    6. Inject ``name:`` from parent directory if missing.
    """
    raw = compose_path.read_text(encoding="utf-8")

    # Build variable table: .env values overridden by actual environment
    variables = {**_load_dotenv(compose_path), **os.environ}

    # Interpolate variables in the raw text
    resolved = _interpolate(raw, variables)

    # Parse with ruamel.yaml for round-trip preservation
    ryaml = YAML()
    data = ryaml.load(resolved)
    if data is None:
        data = {}

    # Apply podlet workarounds
    _strip_image_tags_with_digests(data)
    _expand_single_values(data)
    _strip_extensions(data)
    _inject_build_tags(data)

    # Inject name from parent directory if missing
    if "name" not in data:
        data["name"] = compose_path.parent.resolve().name

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
