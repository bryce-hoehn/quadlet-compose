"""Strip compose extension keys (x-*) for podlet compatibility.

Podlet does not support compose extensions (e.g. ``x-custom``, ``x-env``).
"""


def strip_extensions(data: dict) -> None:
    """Remove all top-level ``x-*`` extension keys from the compose data."""
    for k in [k for k in data if isinstance(k, str) and k.startswith("x-")]:
        del data[k]
