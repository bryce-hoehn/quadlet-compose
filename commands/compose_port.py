"""compose port command — print the public port for a port binding."""


def compose_port(
    *,
    compose_file: str | None = None,
    kube: bool = False,
    detach: bool = False,
    remove_orphans: bool = False,
) -> None:
    """Print the public port for a port binding."""
    raise NotImplementedError("compose port")
