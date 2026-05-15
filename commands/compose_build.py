"""compose build command — build or rebuild services."""


def compose_build(
    *,
    compose_file: str | None = None,
    build_arg: list[str] | None = None,
    builder: str | None = None,
    check: bool = False,
    memory: str | None = None,
    no_cache: bool = False,
    print: bool = False,
    provenance: bool = False,
    pull: bool = False,
    push: bool = False,
    quiet: bool = False,
    sbom: bool = False,
    ssh: str | None = None,
    with_dependencies: bool = False,
) -> None:
    """Build or rebuild services."""
    raise NotImplementedError("compose build")
