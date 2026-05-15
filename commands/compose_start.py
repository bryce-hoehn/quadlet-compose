"""compose start command — start containers without daemon-reload."""

import subprocess

from rich.console import Console

from utils.compose import parse_compose, resolve_compose_path
from utils.mapping import map_compose


def compose_start(
    *,
    compose_file: str | None = None,
) -> None:
    """Start containers without re-writing quadlet files or daemon-reload.

    Unlike ``compose_up``, this assumes quadlet files are already in place.
    It simply starts the systemd units and enables any with
    ``restart: always`` or ``restart: unless-stopped``.
    """
    console = Console()
    compose_path = resolve_compose_path(compose_file)
    compose = parse_compose(compose_path)

    bundle = map_compose(compose, compose_path=compose_path)

    # Start all services
    for svc in bundle.service_names():
        console.print(f"starting {svc}")
        subprocess.run(
            ["systemctl", "--user", "start", svc],
            check=True,
        )

    # Enable services with restart: always / unless-stopped
    for svc, policy in bundle.restart_policies.items():
        if policy in ("always", "unless-stopped"):
            console.print(f"enabling {svc} (restart: {policy})")
            subprocess.run(
                ["systemctl", "--user", "enable", svc],
                check=True,
            )
