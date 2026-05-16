import json
import subprocess
from pathlib import Path

from .compose import ComposeError


def get_unit_directory() -> Path:
    """Get the Podman Quadlet user unit directory.

    Returns ~/.config/containers/systemd/ and creates it if needed.
    """
    unit_dir = Path.home() / ".config" / "containers" / "systemd"
    unit_dir.mkdir(parents=True, exist_ok=True)
    return unit_dir


def find_quadlet_binary() -> str | None:
    """Locate the ``quadlet`` binary shipped with Podman.

    Returns the absolute path as a string, or *None* if not found.
    """

    try:
        result = subprocess.run(
            ["podman", "info", "--format", "json"],
            capture_output=True,
            text=True,
            check=True,
        )
        info = json.loads(result.stdout)
        # Derive libexec dir from the network backend path which
        # lives alongside quadlet (e.g. /usr/libexec/podman/netavark).
        net_path = info.get("host", {}).get("networkBackendInfo", {}).get("path", "")
        if net_path:
            libexec = str(Path(net_path).parent)
            candidate = Path(libexec) / "quadlet"
            if candidate.is_file():
                return str(candidate)
    except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError):
        return None


def run_quadlet_generator(unit_dir: Path | None = None) -> None:
    """Run the Podman Quadlet generator directly.

    This is a reliable alternative to relying on the systemd user generator
    symlink being installed.  Writes generated ``.service`` files to the
    user's ``~/.config/systemd/user/`` directory so that ``systemctl --user
    daemon-reload`` can discover them.

    Raises :class:`ComposeError` if the ``quadlet`` binary cannot be found
    or if the generator exits with an error.
    """
    from . import run_cmd

    quadlet = find_quadlet_binary()
    if quadlet is None:
        raise ComposeError(
            "quadlet binary not found. Install podman or add "
            "quadlet to $PATH / ~/.config/systemd/user-generators/"
        )

    if unit_dir is None:
        unit_dir = get_unit_directory()

    output_dir = Path.home() / ".config" / "systemd" / "user"
    output_dir.mkdir(parents=True, exist_ok=True)

    run_cmd([quadlet, "--user", str(unit_dir)])
