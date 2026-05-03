"""Shared utilities for podlet-compose."""

import os
import subprocess


class ComposeError(Exception):
    """Raised for errors in compose file operations."""


# Global dry-run flag, set by CLI
DRY_RUN = False


def run_cmd(cmd: list[str]) -> subprocess.CompletedProcess:
    """Run a command, raising ComposeError on failure.

    Wraps subprocess.run with unified error handling for missing commands
    and failed executions. In dry-run mode, prints the command instead.
    """
    if DRY_RUN:
        print(f"  [dry-run] {' '.join(cmd)}")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    try:
        return subprocess.run(cmd, check=True, text=True)
    except FileNotFoundError as exc:
        raise ComposeError(f"Command not found: `{cmd[0]}`") from exc
    except subprocess.CalledProcessError as exc:
        raise ComposeError(f"Command failed: {exc.stderr or exc}") from exc
