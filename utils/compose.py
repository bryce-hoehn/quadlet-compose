from pathlib import Path

from compose_spec import PyCompose


# Compose file search order (matches podlet's behavior)
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

    If compose_file is None, searches the CWD following podlet's search order.
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
    c = PyCompose.from_yaml(compose_path)
    d = c.to_dict()
    return d
