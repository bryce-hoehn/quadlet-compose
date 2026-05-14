"""compose restart command — restart service containers."""


def compose_restart(
    *,
    compose_file: str | None = None,
    kube: bool = False,
    detach: bool = False,
    remove_orphans: bool = False,
) -> None:
    """Restart service containers (down + up)."""
    raise NotImplementedError("compose restart")
