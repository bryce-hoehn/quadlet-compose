import subprocess
from typing import Sequence

from .compose import ComposeError, resolve_compose_path, parse_compose
from .quadlet import get_unit_directory


def run_cmd(
    args: Sequence[str] | str,
    *,
    check: bool = False,
    **kwargs: object,
) -> subprocess.CompletedProcess:
    """Run a subprocess command with friendly error handling.

    On failure, raises :class:`ComposeError` with a concise message
    instead of letting the raw :class:`subprocess.CalledProcessError`
    traceback propagate.

    Accepts the same keyword arguments as :func:`subprocess.run`.
    """
    try:
        return subprocess.run(args, check=check, **kwargs)  # type: ignore[arg-type]
    except subprocess.CalledProcessError as exc:
        cmd_str = exc.cmd if isinstance(exc.cmd, str) else " ".join(exc.cmd)
        raise ComposeError(
            f"Command failed (exit {exc.returncode}): {cmd_str}"
        ) from exc


__all__ = [
    "ComposeError",
    "resolve_compose_path",
    "parse_compose",
    "get_unit_directory",
    "run_cmd",
]
