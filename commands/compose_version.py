"""compose version command — show version information."""


def compose_version(
    *,
    compose_file: str | None = None,
    kube: bool = False,
    detach: bool = False,
    remove_orphans: bool = False,
) -> None:
    """Show version information."""
    raise NotImplementedError("compose version")
