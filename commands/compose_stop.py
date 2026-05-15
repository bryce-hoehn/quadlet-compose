"""compose stop command — stop containers without disabling them."""

import subprocess

from rich.console import Console

from utils.compose import parse_compose, resolve_compose_path
from utils.mapping import map_compose


def compose_stop(
    *,
    compose_file: str | None = None,
    timeout: int | None = None,
) -> None:
    """Stop containers without disabling systemd units.

    Unlike ``compose_down``, this does **not** disable or remove units.
    Use ``compose_start`` to resume.
    """
    console = Console()
    compose_path = resolve_compose_path(compose_file)
    compose = parse_compose(compose_path)

    bundle = map_compose(compose, compose_path=compose_path)

    for svc in bundle.service_names():
        cmd = ["systemctl", "--user", "stop", svc]
        if timeout is not None:
            cmd.extend(["--job-mode", "replace-irreversibly"])
        console.print(f"stopping {svc}")
        subprocess.run(cmd, check=True)
