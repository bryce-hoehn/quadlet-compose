"""compose version command — show version information."""

from importlib.metadata import version

from rich.console import Console


def compose_version(
    *,
    compose_file: str | None = None,
    kube: bool = False,
    detach: bool = False,
    remove_orphans: bool = False,
) -> None:
    """Show version information."""
    console = Console()
    console.print(f'quadlet-compose version {version("quadlet-compose")}')
