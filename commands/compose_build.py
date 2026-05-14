"""compose build command — build or rebuild services."""


def compose_build(
    *,
    compose_file: str | None = None,
    kube: bool = False,
    detach: bool = False,
    remove_orphans: bool = False,
) -> None:
    """Build or rebuild services."""
    raise NotImplementedError("compose build")
