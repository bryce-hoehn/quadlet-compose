from .compose_down import compose_down
from .compose_up import compose_up


def compose_restart(
    *, compose_file: str | None = None, no_deps: bool = False, timeout: int = 0
) -> None:
    """Restart service containers (down + up)."""

    compose_down(timeout=timeout)
    compose_up(no_deps=no_deps, timeout=timeout)
