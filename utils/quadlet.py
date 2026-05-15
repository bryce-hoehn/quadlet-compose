import os
from pathlib import Path


def get_unit_directory() -> Path:
    """Get the Podman Quadlet user unit directory.

    Returns ~/.config/containers/systemd/ and creates it if needed.
    """
    unit_dir = Path.home() / ".config" / "containers" / "systemd"
    unit_dir.mkdir(parents=True, exist_ok=True)
    return unit_dir


def enable_service(service_name: str) -> None:
    """Enable a Quadlet-generated user service by creating a symlink.

    ``systemctl --user enable`` refuses to operate on generated units
    (those living under ``/run/user/{uid}/systemd/generator/``) even
    when they carry an ``[Install]`` section.  This helper creates the
    ``WantedBy=default.target`` symlink manually so the service starts
    at user login.

    Args:
        service_name: The systemd service name (e.g. ``jellyfin.service``).
    """
    runtime_dir = os.environ.get(
        'XDG_RUNTIME_DIR',
        f'/run/user/{os.getuid()}',
    )
    generator_service = Path(runtime_dir) / 'systemd' / 'generator' / service_name

    wants_dir = Path.home() / '.config' / 'systemd' / 'user' / 'default.target.wants'
    wants_dir.mkdir(parents=True, exist_ok=True)

    symlink = wants_dir / service_name
    symlink.unlink(missing_ok=True)
    symlink.symlink_to(generator_service)


def disable_service(service_name: str) -> None:
    """Disable a Quadlet-generated user service by removing its symlink.

    Args:
        service_name: The systemd service name (e.g. ``jellyfin.service``).
    """
    wants_dir = Path.home() / '.config' / 'systemd' / 'user' / 'default.target.wants'
    symlink = wants_dir / service_name
    symlink.unlink(missing_ok=True)
