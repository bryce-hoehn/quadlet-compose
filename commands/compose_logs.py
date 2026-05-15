"""compose logs command — view output from containers."""

import subprocess

from utils.compose import get_service_info, parse_compose, resolve_compose_path


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
    subprocess.run(args, check=True)
