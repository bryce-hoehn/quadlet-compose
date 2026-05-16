"""compose start command — start containers without daemon-reload."""

from rich.console import Console

from utils import run_cmd
from utils.compose import parse_compose, resolve_compose_path
from utils.mapping import map_compose


def compose_start(
    *,
    compose_file: str | None = None,
) -> None:
    """Start containers without re-writing quadlet files or daemon-reload.

    Unlike ``compose_up``, this assumes quadlet files are already in place.
    It simply starts the systemd units.  Services with ``restart: always``
    or ``restart: unless-stopped`` are auto-enabled by the Quadlet
    generator via the ``[Install]`` section in the unit file.
    """
    console = Console()
    compose_path = resolve_compose_path(compose_file)
    compose = parse_compose(compose_path)

    bundle = map_compose(compose, compose_path=compose_path)

    # Start all services
    for svc in bundle.service_names():
        console.print(f"starting {svc}")
        run_cmd(["systemctl", "--user", "start", svc])
