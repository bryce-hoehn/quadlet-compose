"""compose pull command — pull service images."""

import subprocess

from typing import Literal
from utils.compose import parse_compose, resolve_compose_path
from utils.mapping import map_compose


def compose_pull(
    *,
    compose_file: str | None = None,
    ignore_buildable: bool = False,
    ignore_pull_failures: bool = False,
    include_deps: bool = False,
    policy: Literal["missing", "always"] | None = None,
    quiet: bool = False,
) -> None:
    """Pull service images."""

    compose_path = resolve_compose_path(compose_file)
    compose = parse_compose(compose_path)

    bundle = map_compose(compose, compose_path=compose_path)

    containers = [
        unit.ContainerName for unit in bundle.containers if unit.ContainerName
    ]

    subprocess.run(["podman", "pull"] + containers, check=True)
