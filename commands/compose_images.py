"""compose images command — list images."""


def compose_images(
    *,
    compose_file: str | None = None,
    kube: bool = False,
    detach: bool = False,
    remove_orphans: bool = False,
) -> None:
    """List images."""
    raise NotImplementedError("compose images")
