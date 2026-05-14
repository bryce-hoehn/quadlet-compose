"""compose top command — display running processes."""

import subprocess

from utils.compose import parse_compose, resolve_compose_path
from utils.mapping import map_compose


def compose_top(
    *,
    compose_file: str | None = None,
    kube: bool = False,
    detach: bool = False,
    remove_orphans: bool = False,
) -> None:
    """Display running processes."""

    compose_path = resolve_compose_path(compose_file)
    compose = parse_compose(compose_path)

    bundle = map_compose(compose, compose_path=compose_path)

    containers = [
        unit.ContainerName for unit in bundle.containers if unit.ContainerName
    ]

    subprocess.run(["podman", "stats"] + containers)
