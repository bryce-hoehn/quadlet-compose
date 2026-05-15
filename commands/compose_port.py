"""compose port command — print the public port for a port binding."""

import subprocess
from typing import Literal

from utils.compose import parse_compose, resolve_compose_path
from utils.mapping import map_compose


def compose_port(
    *,
    compose_file: str | None = None,
    service: str = "",
    private_port: int | None = None,
    protocol: Literal["tcp", "udp"] = "tcp",
    index: int = 1,
) -> None:
    """Print the public port for a port binding."""
    compose_path = resolve_compose_path(compose_file)
    compose = parse_compose(compose_path)

    bundle = map_compose(compose, compose_path=compose_path)

    # Find the container for the given service
    container_name = None
    for unit in bundle.containers:
        if unit.ContainerName == service:
            container_name = unit.ContainerName
            break

    if container_name is None:
        project = bundle.project_name
        for unit in bundle.containers:
            candidate = f"{project}-{service}" if project else service
            if unit.ContainerName == candidate:
                container_name = unit.ContainerName
                break

    if container_name is None:
        raise ValueError(f'Service "{service}" not found in compose file')

    args = ["podman", "port", container_name]
    if private_port is not None:
        args.append(f"{private_port}/{protocol}")

    subprocess.run(args, check=True)
