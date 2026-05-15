"""compose logs command — view output from containers."""

import subprocess

from utils.compose import parse_compose, resolve_compose_path
from utils.mapping import map_compose
from datetime import datetime


def compose_logs(
    *,
    compose_file: str | None = None,
    follow: bool = False,
    index: int = 0,
    no_color: bool = False,
    no_log_prefix: bool = False,
    since: datetime | int = 0,
    tail: int | None = None,
    timestamps: bool = False,
    until: datetime | int = 0,
) -> None:
    """View output from containers."""

    compose_path = resolve_compose_path(compose_file)
    compose = parse_compose(compose_path)

    bundle = map_compose(compose, compose_path=compose_path)

    containers = [
        unit.ContainerName for unit in bundle.containers if unit.ContainerName
    ]

    subprocess.run(["podman", "logs"] + containers, check=True)
