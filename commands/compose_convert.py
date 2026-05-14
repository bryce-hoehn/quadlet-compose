"""compose convert command — preview quadlet files."""


def compose_convert(
    *,
    compose_file: str | None = None,
    kube: bool = False,
    detach: bool = False,
    remove_orphans: bool = False,
) -> None:
    """Preview the generated quadlet files."""
    raise NotImplementedError("compose convert")
