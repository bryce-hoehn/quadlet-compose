import shutil
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

    Searches in order:
      1. ``podman --q <path>`` to ask podman where quadlet lives
      2. ``quadlet`` on ``$PATH``
      3. Common libexec paths (``/usr/libexec/podman/quadlet``,
         ``/usr/lib/podman/quadlet``)

    Returns the absolute path as a string, or *None* if not found.
    """
    # Ask podman directly
    try:
        result = subprocess.run(
            ["podman", "info", "--format", "{{.PodmanLibexecDir}}"],
            capture_output=True,
            text=True,
            check=True,
        )
        libexec = result.stdout.strip()
        if libexec:
            candidate = Path(libexec) / "quadlet"
            if candidate.is_file():
                return str(candidate)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # On PATH as 'quadlet'
    quadlet = shutil.which("quadlet")
    if quadlet:
        return quadlet

    # Common locations
    for p in (
        "/usr/libexec/podman/quadlet",
        "/usr/lib/podman/quadlet",
    ):
        if Path(p).is_file():
            return p

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
