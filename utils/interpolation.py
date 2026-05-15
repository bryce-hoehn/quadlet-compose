"""Variable interpolation for compose files — matches docker-compose behavior.

Uses Python's :class:`string.Template` with a custom subclass that supports
the compose-spec modifier syntax, adapted from docker-compose v1's
``TemplateWithDefaults``.

Supported syntax:

- ``$VAR`` and ``${VAR}`` — direct substitution
- ``$$`` — literal ``$``
- ``${VAR:-default}`` — default if unset or empty
- ``${VAR-default}`` — default if unset
- ``${VAR:?error}`` — error if unset or empty
- ``${VAR?error}`` — error if unset
- ``${VAR:+replacement}`` — replacement if set and non-empty
- ``${VAR+replacement}`` — replacement if set

Before parsing, variables from the ``.env`` file (located alongside the
compose file) are loaded into a mapping via *python-dotenv*.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from string import Template
from typing import Any

import yaml
from dotenv import dotenv_values


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class InvalidInterpolation(Exception):
    """Raised when a string has invalid interpolation syntax."""

    def __init__(self, string: str) -> None:
        self.string = string
        super().__init__(string)


class UnsetRequiredSubstitution(Exception):
    """Raised when a required variable (``${VAR:?err}`` / ``${VAR?err}``) is unset."""

    def __init__(self, custom_err_msg: str) -> None:
        self.err = custom_err_msg
        super().__init__(custom_err_msg)


# ---------------------------------------------------------------------------
# TemplateWithDefaults — adapted from docker-compose v1
# ---------------------------------------------------------------------------

class TemplateWithDefaults(Template):
    """:class:`string.Template` subclass supporting compose-spec modifiers.

    Supports ``:-``, ``-``, ``:?``, ``?``, ``:+``, ``+`` inside braced
    expressions, plus ``$$`` for literal ``$``.
    """

    # Match $, ${VAR}, ${VAR:-default}, $VAR, or $$
    pattern = r"""
        \$(?:
          (?P<escaped>\$)                             |   # $$  → literal $
          (?P<named>[_a-zA-Z][_a-zA-Z0-9]*)           |   # $VAR
          {(?P<braced>[_a-zA-Z][_a-zA-Z0-9]*)         # ${VAR
            (?P<sep>:[-?+]|[-?+])                      # modifier prefix
            (?P<modifier_value>[^}]*)                  # modifier operand
          }                                            |
          {(?P<braced_simple>[_a-zA-Z][_a-zA-Z0-9]*)} |   # ${VAR} (no modifier)
          (?P<invalid>)                                    # bare $ or invalid
        )
    """

    @staticmethod
    def _process_braced_group(
        braced: str,
        sep: str,
        modifier_value: str,
        mapping: dict[str, str],
    ) -> str:
        """Resolve a braced expression with a modifier."""
        var = braced

        if sep == ':-':
            # Default if unset or empty
            return mapping.get(var) or modifier_value

        if sep == '-':
            # Default if unset
            return mapping.get(var, modifier_value)

        if sep == ':?':
            # Required — error if unset or empty
            result = mapping.get(var)
            if not result:
                raise UnsetRequiredSubstitution(modifier_value or var)
            return result

        if sep == '?':
            # Required — error if unset (empty is ok)
            if var not in mapping:
                raise UnsetRequiredSubstitution(modifier_value or var)
            return mapping[var]

        if sep == ':+':
            # Alternative if set and non-empty
            val = mapping.get(var)
            return modifier_value if (val is not None and val) else ''

        if sep == '+':
            # Alternative if set (even if empty)
            return modifier_value if var in mapping else ''

        # Shouldn't reach here
        return mapping.get(var, '')  # type: ignore[unreachable]

    def substitute(self, mapping: dict[str, str]) -> str:  # type: ignore[override]
        """Override to handle compose-spec modifier syntax."""

        def convert(mo: re.Match) -> str:
            # ${VAR} without modifier
            braced_simple = mo.group('braced_simple')
            if braced_simple is not None:
                return mapping.get(braced_simple, '')

            # ${VAR:-default}, ${VAR:?err}, etc.
            braced = mo.group('braced')
            if braced is not None:
                sep = mo.group('sep')
                modifier_value = mo.group('modifier_value') or ''
                return self._process_braced_group(braced, sep, modifier_value, mapping)

            # $VAR (unbraced)
            named = mo.group('named')
            if named is not None:
                return mapping.get(named, '')

            # $$ → literal $
            if mo.group('escaped') is not None:
                return '$'

            # Invalid pattern
            if mo.group('invalid') is not None:
                raise ValueError(f'Invalid interpolation: {self.template}')

            raise ValueError('Unrecognized named group in pattern', self.pattern)

        return self.pattern.sub(convert, self.template)


# ---------------------------------------------------------------------------
# .env file loading
# ---------------------------------------------------------------------------

def _build_variable_map(
    compose_path: Path,
    env_override: dict[str, str] | None = None,
) -> dict[str, str]:
    """Build the variable map for interpolation.

    Priority (highest to lowest):

    1. ``.env`` file in the compose file's parent directory
    2. *env_override* (explicit ``--env KEY=VAL`` from CLI)
    3. Existing ``os.environ`` values
    """
    # Start with os.environ (lowest priority)
    variables: dict[str, str] = dict(os.environ)

    # CLI overrides override os.environ
    if env_override:
        variables.update(env_override)

    # .env file takes top priority
    dotenv_path = compose_path.parent / '.env'
    if dotenv_path.is_file():
        values = dotenv_values(dotenv_path)
        variables.update({k: v for k, v in values.items() if v is not None})

    return variables


# ---------------------------------------------------------------------------
# Recursive interpolation
# ---------------------------------------------------------------------------

def _interpolate_recursive(data: Any, mapping: dict[str, str]) -> Any:
    """Walk a nested dict/list structure and interpolate all string values."""
    if isinstance(data, str):
        try:
            return TemplateWithDefaults(data).substitute(mapping)
        except (ValueError, InvalidInterpolation):
            return data
    if isinstance(data, dict):
        return {
            _interpolate_recursive(k, mapping): _interpolate_recursive(v, mapping)
            for k, v in data.items()
        }
    if isinstance(data, list):
        return [_interpolate_recursive(item, mapping) for item in data]
    return data


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def interpolating_yaml_load(
    compose_path: Path,
    env_override: dict[str, str] | None = None,
) -> dict:
    """Load and interpolate a compose YAML file in one pass.

    1. Builds a variable map from ``os.environ``, CLI overrides, and ``.env``
    2. Parses the YAML with ``yaml.safe_load``
    3. Recursively resolves ``$VAR`` / ``${VAR}`` and modifier syntax
       via :class:`TemplateWithDefaults`

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
    UnsetRequiredSubstitution
        If a required variable (``${VAR:?err}``) is unset/empty.
    """
    from utils.compose import ComposeError

    mapping = _build_variable_map(compose_path, env_override)

    with open(compose_path) as f:
        data = yaml.safe_load(f)

    if data is None:
        raise ComposeError(f'Compose file is empty: {compose_path}')

    return _interpolate_recursive(data, mapping)
