from .stop import compose_stop
from .start import compose_start


def compose_restart(
    *, compose_file: str | None = None, no_deps: bool = False, timeout: int = 0
) -> None:
    """Restart service containers (down + up)."""

    compose_stop(timeout=timeout)
    compose_start()
