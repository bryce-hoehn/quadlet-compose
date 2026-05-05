"""Variable interpolation from .env and environment.

Resolves ``$VAR``, ``${VAR}``, and Docker-style default-value patterns:

- ``$VAR`` / ``${VAR}`` — substitute variable (empty string if unset)
- ``${VAR:-default}`` — use *default* if VAR is unset **or empty**
- ``${VAR-default}`` — use *default* if VAR is unset
- ``${VAR:+alt}`` — use *alt* if VAR is set and non-empty
- ``${VAR+alt}`` — use *alt* if VAR is set (even if empty)
- ``$$`` — literal ``$`` escape

Variables are loaded from a ``.env`` file next to the compose file, with
environment variables taking precedence.
"""

import os
import re
from pathlib import Path

# ---------------------------------------------------------------------------
# .env loader
# ---------------------------------------------------------------------------


def _load_dotenv(compose_path: Path) -> dict[str, str]:
    """Load variables from a .env file next to the compose file."""
    env_path = compose_path.parent.resolve() / ".env"
    if not env_path.is_file():
        return {}
    env = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            env[key.strip()] = value.strip().strip("\"'")
    return env


# ---------------------------------------------------------------------------
# Interpolation engine
# ---------------------------------------------------------------------------

# Matches $$, ${...}, or $VAR
_PATTERN = re.compile(
    r"\$\$"                     # $$  → literal $
    r"|\$\{([^}]+)\}"           # ${...} forms (capture inner content)
    r"|\$([A-Za-z_]\w*)"        # $VAR form
)


def _substitute(text: str, variables: dict[str, str]) -> str:
    """Replace variable patterns in *text* using *variables*."""

    def _replace(match: re.Match) -> str:
        # $$ → literal $
        if match.group(0) == "$$":
            return "$"

        # $VAR form (group 2)
        if match.group(2) is not None:
            return variables.get(match.group(2), "")

        # ${...} form — parse inner content (group 1)
        inner = match.group(1)

        # ${VAR:-default} — default if unset or empty
        m = re.match(r"([A-Za-z_]\w*):-(.*)", inner, re.DOTALL)
        if m:
            val = variables.get(m.group(1))
            return val if val else m.group(2)

        # ${VAR:+alt} — alt if set and non-empty
        m = re.match(r"([A-Za-z_]\w*):\+(.*)", inner, re.DOTALL)
        if m:
            val = variables.get(m.group(1))
            return m.group(2) if val else ""

        # ${VAR-default} — default if unset
        m = re.match(r"([A-Za-z_]\w*)-(.*)", inner, re.DOTALL)
        if m:
            var_name = m.group(1)
            return variables[var_name] if var_name in variables else m.group(2)

        # ${VAR+alt} — alt if set (even if empty)
        m = re.match(r"([A-Za-z_]\w*)\+(.*)", inner, re.DOTALL)
        if m:
            var_name = m.group(1)
            return m.group(2) if var_name in variables else ""

        # ${VAR} — plain substitution
        return variables.get(inner, "")

    return _PATTERN.sub(_replace, text)


# ---------------------------------------------------------------------------
# Public hack entry point
# ---------------------------------------------------------------------------


def interpolate(raw_text: str, compose_path: Path) -> str:
    """Interpolate ``$VAR`` / ``${VAR}`` patterns in *raw_text*.

    Builds a variable table from ``.env`` + ``os.environ`` and substitutes
    all occurrences.  Unresolved variables become empty strings.
    """
    variables = {**_load_dotenv(compose_path), **os.environ}
    return _substitute(raw_text, variables)
