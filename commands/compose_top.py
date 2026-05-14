"""compose top command — display running processes."""


def compose_top(
    *,
    compose_file: str | None = None,
    kube: bool = False,
    detach: bool = False,
    remove_orphans: bool = False,
) -> None:
    """Display running processes."""
    raise NotImplementedError("compose top")
