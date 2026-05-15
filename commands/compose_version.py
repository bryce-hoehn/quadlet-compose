"""compose version command — show version information."""

from importlib.metadata import version

from typing import Literal

from rich.console import Console


def compose_version(
    *,
    _format: Literal["pretty", "json"] = "pretty",
    short: bool = False,
) -> None:
    """Show version information."""
    console = Console()

    if short:
        console.print(version("quadlet-compose"))

    elif _format == "json":
        v = version("quadlet-compose")
        console.print(f'{{"version": "v{v}"}}')

    else:
        console.print(f'Quadlet Compose version v{version("quadlet-compose")}')
