"""Variable interpolation for compose files — matches docker-compose behavior.

Uses :func:`os.path.expandvars` for ``$VAR`` / ``${VAR}`` resolution.
Before parsing, variables from the ``.env`` file (located alongside the
compose file) are loaded into ``os.environ`` via *python-dotenv* so that
``expandvars`` can resolve them.  The ``.env`` file takes priority over
 any existing environment variables.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import dotenv_values


class InterpolationError(Exception):
    """Raised when variable interpolation fails."""


# ---------------------------------------------------------------------------
# Environment loading
# ---------------------------------------------------------------------------

def _apply_env(
    compose_path: Path,
    env_override: dict[str, str] | None = None,
) -> None:
    """Load variables into ``os.environ`` for :func:`os.path.expandvars`.

    Priority (highest to lowest):

    1. ``.env`` file in the compose file's parent directory
    2. *env_override* (explicit ``--env KEY=VAL`` from CLI)
    3. Existing ``os.environ`` values
    """
    # Apply CLI overrides first (lower priority than .env)
    if env_override:
        os.environ.update(env_override)

    # .env file takes top priority — applied last so it wins
    dotenv_path = compose_path.parent / '.env'
    if dotenv_path.is_file():
        values = dotenv_values(dotenv_path)
        os.environ.update({k: v for k, v in values.items() if v is not None})


# ---------------------------------------------------------------------------
# Recursive interpolation
# ---------------------------------------------------------------------------

def _interpolate_recursive(data: Any) -> Any:
    """Walk a nested dict/list structure and interpolate all string values."""
    if isinstance(data, str):
        return os.path.expandvars(data)
    if isinstance(data, dict):
        return {_interpolate_recursive(k): _interpolate_recursive(v) for k, v in data.items()}
    if isinstance(data, list):
        return [_interpolate_recursive(item) for item in data]
    return data


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def interpolating_yaml_load(
    compose_path: Path,
    env_override: dict[str, str] | None = None,
) -> dict:
    """Load and interpolate a compose YAML file in one pass.

    1. Loads ``.env`` file variables into ``os.environ``
    2. Parses the YAML with ``yaml.safe_load``
    3. Recursively resolves ``$VAR`` / ``${VAR}`` via :func:`os.path.expandvars`

    Parameters
    ----------
    compose_path:
        Path to the compose file.
    env_override:
        Optional explicit env vars from CLI ``--env`` flags.

    Returns
    -------
    dict
        Interpolated compose data.

    Raises
    ------
    ComposeError
        If the file is empty.
    """
    from utils.compose import ComposeError

    _apply_env(compose_path, env_override)

    with open(compose_path) as f:
        data = yaml.safe_load(f)

    if data is None:
        raise ComposeError(f'Compose file is empty: {compose_path}')

    return _interpolate_recursive(data)
