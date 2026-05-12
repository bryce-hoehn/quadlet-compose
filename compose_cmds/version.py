"""compose_version - Show version information."""

from importlib.metadata import PackageNotFoundError, version


def compose_version(**_kwargs) -> None:
    """Print the quadlet-compose version."""
    try:
        v = version("quadlet-compose")
    except PackageNotFoundError:
        print("quadlet-compose (development)")
        return
    print(f"quadlet-compose version {v}")
