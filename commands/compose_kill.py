"""compose kill command — kill containers."""

import subprocess

from rich.console import Console

from utils.compose import get_service_info, parse_compose, resolve_compose_path


def compose_kill(
    *,
    compose_file: str | None = None,
    signal: str | None = None,
) -> None:
    """Kill containers by sending SIGKILL (or custom signal)."""
    console = Console()
    compose_path = resolve_compose_path(compose_file)
    compose = parse_compose(compose_path)

    info = get_service_info(compose, compose_path=compose_path)

    for svc_name in info.service_names:
        container_name = info.container_names[svc_name]
        unit_name = f"{container_name}-container.service"
        console.print(f"killing {unit_name}")
        kill_args = ["systemctl", "--user", "kill", unit_name]
        if signal:
            kill_args.extend(["--signal", signal])
        subprocess.run(kill_args, check=True)
