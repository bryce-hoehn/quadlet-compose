"""Inject ``name:`` from parent directory if missing.

``podlet compose --pod`` requires a top-level ``name:`` field in the
compose file.  This hack automatically injects the parent directory name
as the project name when the field is absent.
"""

from pathlib import Path


def name_inject(data: dict, compose_path: Path) -> None:
    """Inject ``name:`` from the compose file's parent directory if missing."""
    if "name" not in data:
        data["name"] = compose_path.parent.resolve().name
