import os
from pathlib import Path


def get_unit_directory() -> Path:
    """Get the Podman Quadlet user unit directory.

    Returns ~/.config/containers/systemd/ and creates it if needed.
    """
    unit_dir = Path.home() / ".config" / "containers" / "systemd"
    unit_dir.mkdir(parents=True, exist_ok=True)
    return unit_dir