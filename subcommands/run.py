"""compose run command — run a one-off command in a new container."""

from rich.console import Console

from utils import run_cmd
from utils.compose import parse_compose, resolve_compose_path
from utils.mapping import map_compose

HELP = "Run a one-off command in a new container"
ARGS = [
    ("service", {"help": "Service name"}),
    ("command", {"nargs": "*", "help": "Command and arguments"}),
    (
        "--build",
        {
            "action": "store_true",
            "default": False,
            "help": "Build images before starting",
        },
    ),
    (
        ("-d", "--detach"),
        {
            "action": "store_true",
            "default": False,
            "dest": "detach",
            "help": "Run in background",
        },
    ),
    (
        "--entrypoint",
        {
            "default": None,
            "help": "Override entrypoint",
        },
    ),
    (
        ("-e", "--env"),
        {
            "action": "append",
            "default": None,
            "dest": "env",
            "help": "Set environment variables",
        },
    ),
    (
        "--label",
        {
            "action": "append",
            "default": None,
            "help": "Add metadata to container",
        },
    ),
    (
        ("--name",),
        {
            "default": None,
            "help": "Assign a name to the container",
        },
    ),
    (
        "--no-deps",
        {
            "action": "store_true",
            "default": False,
            "help": "Don't start linked services",
        },
    ),
    (
        ("-p", "--publish"),
        {
            "action": "append",
            "default": None,
            "dest": "publish",
            "help": "Publish a port",
        },
    ),
    (
        ("-q", "--quiet"),
        {
            "action": "store_true",
            "default": False,
            "dest": "quiet",
            "help": "Suppress pull output",
        },
    ),
    (
        ("--rm",),
        {
            "action": "store_true",
            "default": False,
            "dest": "remove",
            "help": "Remove container after run",
        },
    ),
    (
        ("-u", "--user"),
        {
            "default": None,
            "dest": "user",
            "help": "Run as this user",
        },
    ),
    (
        ("-v", "--volume"),
        {
            "action": "append",
            "default": None,
            "dest": "volume",
            "help": "Bind mount a volume",
        },
    ),
    (
        ("-w", "--workdir"),
        {
            "default": None,
            "dest": "workdir",
            "help": "Working directory inside the container",
        },
    ),
]


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

    run_cmd(args)
