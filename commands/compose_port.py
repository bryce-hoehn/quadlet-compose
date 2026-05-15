"""compose port command — print the public port for a port binding."""

from typing import Literal


def compose_port(
    *,
    compose_file: str | None = None,
    protocol: Literal["tcp", "udp"] = "tcp",
    index: int = 1,
) -> None:
    """Print the public port for a port binding."""
    raise NotImplementedError("compose port")
