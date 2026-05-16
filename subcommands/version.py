"""compose version command — show version information."""

from importlib.metadata import version

from typing import Literal

from rich.console import Console

HELP = "Show version information"
ARGS = [
    (
        ("-f", "--format"),
        {
            "choices": ["pretty", "json"],
            "default": "pretty",
            "dest": "_format",
            "help": "Output format",
        },
    ),
    (
        "--short",
        {
            "action": "store_true",
            "default": False,
            "help": "Show only version number",
        },
    ),
]


def compose_version(
    *,
    compose_file: str | None = None,
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
