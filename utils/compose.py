"""Compose file parsing and resolution."""

import os
import tempfile
from collections import defaultdict
from pathlib import Path
from string import Template

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


def _iter_services(data: dict):
    """Yield ``(name, service_dict)`` for each valid service entry."""
    services = data.get("services")
    if not services:
        return
    for name, svc in services.items():
        if isinstance(svc, dict):
            yield name, svc


def _normalize_service_fields(data: dict) -> None:
    """Apply per-service field normalizations that podlet cannot handle.

    - Strip image tags when a digest is also present
      (``image:foo:v1@sha256:abc`` → ``image:foo@sha256:abc``).
    - Strip ``hostname`` and ``network_mode``
      (incompatible with shared pod UTS/network namespaces).
    - Fix ``depends_on`` entries with unsupported conditions
      (``service_healthy``, ``service_completed_successfully``) and
      ``restart: true`` without ``required: true``.  Preserves
      ``required`` and ``restart`` flags that podlet translates to
      systemd ``Requires=`` / ``BindsTo=``.
    - Strip ``configs`` (not supported by podlet).
    - Strip non-external ``secrets`` (only external secrets supported).
    """
    _UNSUPPORTED_CONDITIONS = {"service_healthy", "service_completed_successfully"}

    for _name, svc in _iter_services(data):
        # Strip image tag when digest is present
        image = svc.get("image")
        if isinstance(image, str) and "@" in image and ":" in image.split("@")[0]:
            at_idx = image.index("@")
            last_colon = image.rfind(":", 0, at_idx)
            if last_colon > 0:
                svc["image"] = image[:last_colon] + image[at_idx:]

        # Strip pod-incompatible fields
        for key in ("hostname", "network_mode"):
            svc.pop(key, None)

        # Fix depends_on — only strip what podlet can't handle
        dep = svc.get("depends_on")
        if isinstance(dep, dict):
            cleaned = {}
            all_reduced = True
            for dep_name, dep_config in dep.items():
                if not isinstance(dep_config, dict):
                    cleaned[dep_name] = dep_config
                    continue
                # Strip unsupported conditions (defaults to service_started)
                if dep_config.get("condition") in _UNSUPPORTED_CONDITIONS:
                    dep_config.pop("condition", None)
                # restart=true without required=true is unsupported by podlet
                if dep_config.get("restart") and not dep_config.get("required"):
                    dep_config.pop("restart", None)
                if dep_config:
                    cleaned[dep_name] = dep_config
                    all_reduced = False
                else:
                    cleaned[dep_name] = None
            # If all entries were reduced to None, use short form
            if all_reduced:
                svc["depends_on"] = list(cleaned.keys())
            else:
                svc["depends_on"] = cleaned

        # Strip configs (not supported by podlet)
        svc.pop("configs", None)

        # Strip non-external secrets
        secrets = svc.get("secrets")
        if isinstance(secrets, list):
            external = [s for s in secrets if isinstance(s, dict) and s.get("external")]
            if external:
                svc["secrets"] = external
            else:
                svc.pop("secrets", None)


def _expand_single_values(data: dict) -> None:
    """Auto-expand single-value entries in devices, ports, and volumes.

    Docker-compose allows short forms like ``devices: ["/dev/dri"]`` or
    ``ports: ["8080"]``.  Podlet requires the full ``host:container`` form.
    """
    for _name, svc in _iter_services(data):
        # Expand devices and ports (simple colon duplication)
        for key in ("devices", "ports"):
            items = svc.get(key)
            if not isinstance(items, list):
                continue
            svc[key] = [
                f"{item}:{item}" if isinstance(item, str) and ":" not in item else item
                for item in items
            ]

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


def _strip_extensions(data: dict) -> None:
    """Remove all top-level ``x-*`` extension keys from the compose data.

    Podlet does not support compose extensions (e.g. ``x-custom``, ``x-env``).
    """
    for k in [k for k in data if isinstance(k, str) and k.startswith("x-")]:
        del data[k]


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
    2. Normalize service fields — strip image tags with digests,
       remove pod-incompatible fields (``hostname``, ``network_mode``),
       fix unsupported ``depends_on`` conditions, strip ``configs``
       and non-external ``secrets``.
    3. Auto-expand single-value devices, ports, and path-like volumes.
    4. Remove ``x-*`` compose extension keys.
    5. Inject ``name:`` from parent directory if missing.

    Note: ``build:`` is now handled natively by podlet v0.3.1+ which
    generates ``.build`` Quadlet files.  No pre-build step is needed.
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
    _normalize_service_fields(data)
    _expand_single_values(data)
    _strip_extensions(data)

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
