"""compose logs command — view output from containers."""

from utils import run_cmd
from utils.compose import get_service_info, parse_compose, resolve_compose_path

HELP = "View output from containers"
ARGS = [
    (
        ("-f", "--follow"),
        {
            "action": "store_true",
            "default": False,
            "dest": "follow",
            "help": "Follow log output",
        },
    ),
    ("--index", {"type": int, "default": 0, "help": "Index of the container"}),
    (
        "--no-color",
        {
            "action": "store_true",
            "default": False,
            "help": "Produce monochrome output",
        },
    ),
    (
        "--no-log-prefix",
        {
            "action": "store_true",
            "default": False,
            "help": "Don't print prefix in logs",
        },
    ),
    (
        "--since",
        {"default": 0, "help": "Show logs since timestamp or relative time"},
    ),
    (
        "--tail",
        {
            "type": int,
            "default": None,
            "help": "Number of lines to show from end",
        },
    ),
    (
        ("-t", "--timestamps"),
        {
            "action": "store_true",
            "default": False,
            "dest": "timestamps",
            "help": "Show timestamps",
        },
    ),
    (
        "--until",
        {"default": 0, "help": "Show logs before timestamp or relative time"},
    ),
]


def compose_logs(
    *,
    compose_file: str | None = None,
    follow: bool = False,
    index: int = 0,
    no_color: bool = False,
    no_log_prefix: bool = False,
    since: str | int | None = None,
    tail: int | None = None,
    timestamps: bool = False,
    until: str | int | None = None,
) -> None:
    """View output from containers."""

    compose_path = resolve_compose_path(compose_file)
    compose = parse_compose(compose_path)

    info = get_service_info(compose, compose_path=compose_path)

    containers = list(info.container_names.values())

    args = ["podman", "logs"]

    if follow:
        args.append("--follow")
    if since is not None:
        args.extend(["--since", str(since)])
    if tail is not None:
        args.extend(["--tail", str(tail)])
    if timestamps:
        args.append("--timestamps")
    if until is not None:
        args.extend(["--until", str(until)])

    args.extend(containers)
    run_cmd(args)
