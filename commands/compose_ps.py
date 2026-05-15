"""compose ps command — list containers."""

import subprocess

from typing import Literal
from utils.compose import parse_compose, resolve_compose_path
from utils.mapping import map_compose


def compose_ps(
    *,
    compose_file: str | None = None,
    _all: bool = False,
    _filter: (
        Literal[
            "paused", "restarting", "removing", "running", "dead", "created", "exited"
        ]
        | None
    ) = None,
    _format: Literal["pretty", "json"] = "pretty",
    no_trunc: bool = False,
    orphans: bool = True,
    quiet: bool = False,
    services: bool = False,
    status: (
        Literal[
            "paused", "restarting", "removing", "running", "dead", "created", "exited"
        ]
        | None
    ) = None,
) -> None:
    """List containers."""

    compose_path = resolve_compose_path(compose_file)
    compose = parse_compose(compose_path)

    bundle = map_compose(compose, compose_path=compose_path)

    containers = [
        unit.ContainerName for unit in bundle.containers if unit.ContainerName
    ]

    subprocess.run(["podman", "ps"] + containers, check=True)
