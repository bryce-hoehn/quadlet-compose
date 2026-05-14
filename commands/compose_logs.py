"""compose logs command — view output from containers."""


def compose_logs(
    *,
    compose_file: str | None = None,
    kube: bool = False,
    detach: bool = False,
    remove_orphans: bool = False,
) -> None:
    """View output from containers."""
    raise NotImplementedError("compose logs")
