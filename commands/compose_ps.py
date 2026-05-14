"""compose ps command — list containers."""


def compose_ps(
    *,
    compose_file: str | None = None,
    kube: bool = False,
    detach: bool = False,
    remove_orphans: bool = False,
) -> None:
    """List containers."""
    raise NotImplementedError("compose ps")
