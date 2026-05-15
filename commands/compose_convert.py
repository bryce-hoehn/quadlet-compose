"""compose convert command — preview quadlet files."""

from typing import Literal


def compose_convert(
    *,
    compose_file: str | None = None,
    _format: Literal["yaml", "json"] = "yaml",
    hash: bool = False,
    images: bool = False,
    no_consistency: bool = False,
    no_interpolate: bool = False,
    no_normalize: bool = False,
    output: str | None = None,
    profiles: bool = False,
    quiet: bool = False,
    resolve_image_digests: bool = False,
    services: bool = False,
    volumes: bool = False,
) -> None:
    """Preview the generated quadlet files."""
    raise NotImplementedError("compose convert")
