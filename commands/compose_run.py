"""compose run command — run a one-off command in a new container."""

import subprocess

from rich.console import Console

from utils.compose import parse_compose, resolve_compose_path
from utils.mapping import map_compose


def compose_run(
    *,
    compose_file: str | None = None,
    service: str = "",
    command: list[str] | None = None,
    build: bool = False,
    detach: bool = False,
    entrypoint: str | None = None,
    env: list[str] | None = None,
    interactive: bool = True,
    label: list[str] | None = None,
    name: str | None = None,
    no_deps: bool = False,
    publish: list[str] | None = None,
    quiet: bool = False,
    remove: bool = False,
    tty: bool = True,
    use_aliases: bool = False,
    user: str | None = None,
    volume: list[str] | None = None,
    workdir: str | None = None,
) -> None:
    """Run a one-off command in a new container."""
    console = Console()
    compose_path = resolve_compose_path(compose_file)
    compose = parse_compose(compose_path)

    bundle = map_compose(compose, compose_path=compose_path)

    # Find the container unit for the given service
    container_unit = None
    for unit in bundle.containers:
        if unit.ContainerName == service:
            container_unit = unit
            break

    if container_unit is None:
        project = bundle.project_name
        for unit in bundle.containers:
            candidate = f"{project}-{service}" if project else service
            if unit.ContainerName == candidate:
                container_unit = unit
                break

    if container_unit is None:
        raise ValueError(f'Service "{service}" not found in compose file')

    image = container_unit.Image
    if not image:
        raise ValueError(f'Service "{service}" has no image defined')

    # Build podman run args
    args = ["podman", "run"]

    if not interactive:
        args.append("-i")
    if not tty:
        args.append("-t")
    if detach:
        args.append("-d")
    if entrypoint:
        args.extend(["--entrypoint", entrypoint])
    if env:
        for e in env:
            args.extend(["--env", e])
    if label:
        for l in label:
            args.extend(["--label", l])
    if name:
        args.extend(["--name", name])
    if publish:
        for p in publish:
            args.extend(["--publish", p])
    if remove:
        args.append("--rm")
    if user:
        args.extend(["--user", user])
    if volume:
        for v in volume:
            args.extend(["--volume", v])
    if workdir:
        args.extend(["--workdir", workdir])

    args.append(image)

    if command:
        args.extend(command)

    subprocess.run(args, check=True)
