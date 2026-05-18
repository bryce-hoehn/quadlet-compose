"""Shared helper utilities for quadlet-compose internals."""

HASH_LABEL_PREFIX = "Label=io.quadlet-compose.hash="

#: Maps quadlet file extension → suffix Quadlet appends to the stem
#: when generating the systemd service name.
SERVICE_SUFFIX: dict[str, str] = {
    ".container": "",
    ".pod": "-pod",
    ".network": "-network",
    ".volume": "-volume",
    ".build": "-build",
}


def quadlet_to_service(filename: str) -> str:
    """Convert a quadlet filename to its systemd service name."""
    stem, ext = filename.rsplit(".", 1)
    suffix = SERVICE_SUFFIX.get(f".{ext}", "")
    return f"{stem}{suffix}.service"


def extract_hash(content: str) -> str | None:
    """Extract the content hash from quadlet file content.

    Returns the hex digest or ``None`` if no hash label is found.
    """
    for line in content.splitlines():
        if line.startswith(HASH_LABEL_PREFIX):
            return line[len(HASH_LABEL_PREFIX) :]
    return None
