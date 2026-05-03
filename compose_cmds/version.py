"""compose_version - Show version information."""

from importlib.metadata import PackageNotFoundError, version


def compose_version(**_kwargs) -> None:
    """Print the podlet-compose version."""
    try:
        v = version("podlet-compose")
    except PackageNotFoundError:
        print("podlet-compose (development)")
        return
    print(f"podlet-compose version {v}")
