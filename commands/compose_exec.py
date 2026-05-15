"""compose exec command — execute a command in a running service container."""

import subprocess

from rich.console import Console

from utils.compose import parse_compose, resolve_compose_path
from utils.mapping import map_compose


def compose_exec(
    *,
    compose_file: str | None = None,
    service: str = "",
    command: list[str] | None = None,
    detach: bool = False,
    env: list[str] | None = None,
    index: int = 1,
    interactive: bool = True,
    no_tty: bool = False,
    privileged: bool = False,
    user: str | None = None,
    workdir: str | None = None,
) -> None:
    """Execute a command in a running service container."""
    console = Console()
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
        # Try matching by service name with project prefix
        project = bundle.project_name
        for unit in bundle.containers:
            candidate = f"{project}-{service}" if project else service
            if unit.ContainerName == candidate:
                container_name = unit.ContainerName
                break

    if container_name is None:
        raise ValueError(f'Service "{service}" not found in compose file')

    # Build podman exec args
    podman_args = ["podman", "exec"]

    if detach:
        podman_args.append("--detach")
    if not interactive and not detach:
        podman_args.append("--interactive")
    if no_tty:
        podman_args.append("--tty=false")
    if privileged:
        podman_args.append("--privileged")
    if user:
        podman_args.extend(["--user", user])
    if workdir:
        podman_args.extend(["--workdir", workdir])
    if env:
        for e in env:
            podman_args.extend(["--env", e])

    podman_args.append(container_name)

    if command:
        podman_args.extend(command)

    subprocess.run(podman_args, check=True)
