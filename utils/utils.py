"""Shared utilities for podlet-compose."""

import os
import subprocess


class ComposeError(Exception):
    """Raised for errors in compose file operations."""


# Global dry-run flag, set by CLI
DRY_RUN = False


def run_cmd(cmd: list[str], *, quiet: bool = False) -> subprocess.CompletedProcess:
    """Run a command, raising ComposeError on failure.

    Wraps subprocess.run with unified error handling for missing commands
    and failed executions. In dry-run mode, prints the command instead.

    When *quiet* is True, stdout and stderr are captured (not printed).
    """
    if DRY_RUN:
        print(f"  [dry-run] {' '.join(cmd)}")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    try:
        return subprocess.run(
            cmd,
            check=True,
            text=True,
            stdout=subprocess.PIPE if quiet else None,
            stderr=subprocess.PIPE if quiet else None,
        )
    except FileNotFoundError as exc:
        raise ComposeError(f"Command not found: `{cmd[0]}`") from exc
    except subprocess.CalledProcessError as exc:
        parts = [f"Command `{' '.join(cmd)}` failed (exit {exc.returncode})"]
        if exc.stderr and exc.stderr.strip():
            parts.append(exc.stderr.strip())
        try:
            journal = subprocess.run(
                ["journalctl", "--user", "-n", "10", "--no-pager"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if journal.stdout and journal.stdout.strip():
                parts.append(journal.stdout.strip())
        except Exception:
            pass
        raise ComposeError("\n".join(parts)) from exc
