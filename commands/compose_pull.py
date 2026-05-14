"""compose pull command — pull service images."""


def compose_pull(
    *,
    compose_file: str | None = None,
    kube: bool = False,
    detach: bool = False,
    remove_orphans: bool = False,
) -> None:
    """Pull service images."""
    raise NotImplementedError("compose pull")
