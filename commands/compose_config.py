"""compose config command — validate and view compose config."""


def compose_config(
    *,
    compose_file: str | None = None,
    kube: bool = False,
    detach: bool = False,
    remove_orphans: bool = False,
) -> None:
    """Validate and view the compose file configuration."""
    raise NotImplementedError("compose config")
