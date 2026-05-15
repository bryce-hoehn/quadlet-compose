"""compose config command — validate and view compose config."""

from typing import Literal


def compose_config(
    *,
    compose_file: str | None = None,
    _format: Literal["yaml", "json"] = "yaml",
    environment: bool = False,
    hash: str | None = None,
    images: bool = False,
    lock_image_digests: bool = False,
    models: bool = False,
    networks: bool = False,
    no_consistency: bool = False,
    no_env_resolution: bool = False,
    no_interpolate: bool = False,
    no_normalize: bool = False,
    no_path_resolution: bool = False,
    output: str | None = None,
    profiles: bool = False,
    quiet: bool = False,
    resolve_image_digests: bool = False,
    services: bool = False,
    variables: bool = False,
    volumes: bool = False,
) -> None:
    """Validate and view the compose file configuration."""
    raise NotImplementedError("compose config")
