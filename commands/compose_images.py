"""compose images command — list images."""

import subprocess

from typing import Literal

from rich.console import Console
from utils.compose import get_service_info, parse_compose, resolve_compose_path


def compose_images(
    *,
    compose_file: str | None = None,
    _format: Literal["table", "json"] = "table",
    quiet: bool = False,
) -> None:
    """List images."""

    console = Console()
    compose_path = resolve_compose_path(compose_file)
    compose = parse_compose(compose_path)

    info = get_service_info(compose, compose_path=compose_path)

    label = f"io.quadlet-compose.project={info.project_name}"
    subprocess.run(["podman", "images", "--filter", f"label={label}"], check=True)
