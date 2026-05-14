"""compose down command — stop and remove containers."""


def compose_down(
    *,
    compose_file: str | None = None,
    kube: bool = False,
    detach: bool = False,
    remove_orphans: bool = False,
) -> None:
    """Stop and remove containers, networks, volumes, and images."""
    raise NotImplementedError("compose down")
