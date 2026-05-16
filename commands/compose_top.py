"""compose top command — display running processes."""

from rich.console import Console

from utils import run_cmd
from utils.compose import get_service_info, parse_compose, resolve_compose_path


def compose_top(
    *,
    compose_file: str | None = None,
    services: list[str] | None = None,
) -> None:
    """Display running processes."""

    console = Console()
    compose_path = resolve_compose_path(compose_file)
    compose = parse_compose(compose_path)

    info = get_service_info(compose, compose_path=compose_path)

    if services:
        # Filter to specific services
        containers = []
        for svc in services:
            name = info.container_names.get(svc)
            if name:
                containers.append(name)
    else:
        containers = list(info.container_names.values())

    if not containers:
        console.print("[yellow]No running containers found.[/yellow]")
        return

    run_cmd(["podman", "stats"] + containers)
