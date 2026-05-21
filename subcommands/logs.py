"""compose logs command — view output from containers."""

import json
import subprocess
from datetime import datetime, timezone

from rich.console import Console

from utils import ComposeError, run_cmd
from utils.compose import get_service_info, parse_compose, resolve_compose_path

HELP = "View output from containers"
ARGS = [
    (
        ("-f", "--follow"),
        {
            "action": "store_true",
            "default": False,
            "dest": "follow",
            "help": "Follow log output",
        },
    ),
    ("--index", {"type": int, "default": 0, "help": "Index of the container"}),
    (
        "--no-color",
        {
            "action": "store_true",
            "default": False,
            "help": "Produce monochrome output",
        },
    ),
    (
        "--no-log-prefix",
        {
            "action": "store_true",
            "default": False,
            "help": "Don't print prefix in logs",
        },
    ),
    (
        "--since",
        {"default": None, "help": "Show logs since timestamp or relative time"},
    ),
    (
        "--tail",
        {
            "type": int,
            "default": None,
            "help": "Number of lines to show from end",
        },
    ),
    (
        ("-t", "--timestamps"),
        {
            "action": "store_true",
            "default": False,
            "dest": "timestamps",
            "help": "Show timestamps",
        },
    ),
    (
        "--until",
        {"default": None, "help": "Show logs before timestamp or relative time"},
    ),
]


def _format_journal_line(
    line: str,
    *,
    no_log_prefix: bool = False,
    timestamps: bool = False,
    console: Console,
) -> None:
    """Parse a single ``journalctl --output=json`` line and print it."""
    line = line.strip()
    if not line:
        return

    try:
        entry = json.loads(line)
    except json.JSONDecodeError:
        console.print(line, highlight=False)
        return

    message = entry.get("MESSAGE", "")
    if not message:
        return

    if isinstance(message, list):
        message = bytes(b & 0xFF for b in message).decode(
            "utf-8",
            errors="replace",
        )

    parts: list[str] = []

    if timestamps:
        ts_raw = entry.get("__REALTIME_TIMESTAMP")
        if ts_raw:
            ts_us = int(ts_raw)
            ts = datetime.fromtimestamp(ts_us / 1_000_000, tz=timezone.utc)
            parts.append(
                ts.strftime("%Y-%m-%dT%H:%M:%S") + f".{ts.microsecond:06d}Z",
            )

    if not no_log_prefix:
        unit = entry.get(
            "_SYSTEMD_UNIT",
            entry.get("SYSLOG_IDENTIFIER", ""),
        )
        prefix = unit.removesuffix(".service") if unit else ""
        parts.append(f"{prefix} |")

    console.print(" ".join(parts) + (" " if parts else "") + message, highlight=False)


def _run_journalctl_json(
    journal_args: list[str],
    *,
    follow: bool = False,
    no_color: bool = False,
    no_log_prefix: bool = False,
    timestamps: bool = False,
) -> None:
    """Run ``journalctl --output=json`` and format entries in Python."""
    console = Console(no_color=no_color)
    args = journal_args + ["--output=json"]

    if follow:
        proc = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        try:
            if proc.stdout is not None:
                for line in proc.stdout:
                    _format_journal_line(
                        line,
                        no_log_prefix=no_log_prefix,
                        timestamps=timestamps,
                        console=console,
                    )
        except KeyboardInterrupt:
            pass
        finally:
            proc.terminate()
            proc.wait()
    else:
        result = subprocess.run(args, capture_output=True, text=True)
        for line in result.stdout.splitlines():
            _format_journal_line(
                line,
                no_log_prefix=no_log_prefix,
                timestamps=timestamps,
                console=console,
            )


def compose_logs(
    *,
    compose_file: str | None = None,
    follow: bool = False,
    index: int = 0,
    no_color: bool = False,
    no_log_prefix: bool = False,
    since: str | int | None = None,
    tail: int | None = None,
    timestamps: bool = False,
    until: str | int | None = None,
) -> None:
    """View output from containers.

    When the containers exist in Podman, ``podman logs`` is used
    directly.  If the containers have not been created (e.g. the
    service failed to start), the function falls back to
    ``journalctl --output=json`` for the corresponding systemd units.
    Journal entries are parsed and re-formatted in Python so that
    long lines are never truncated by a pager.
    """

    compose_path = resolve_compose_path(compose_file)
    compose = parse_compose(compose_path)

    info = get_service_info(compose, compose_path=compose_path)

    containers = list(info.container_names.values())

    args = ["podman", "logs"]

    if not no_log_prefix:
        args.append("--names")
    if not no_color:
        args.append("--color")
    if follow:
        args.append("--follow")
    if since is not None:
        args.extend(["--since", str(since)])
    if tail is not None:
        args.extend(["--tail", str(tail)])
    if timestamps:
        args.append("--timestamps")
    if until is not None:
        args.extend(["--until", str(until)])

    args.extend(containers)

    try:
        run_cmd(args, check=True)
    except ComposeError:
        # Containers may not exist (e.g. failed to start).  Fall back
        # to journalctl so the user can still see systemd / podman
        # output for the service.
        journal_args = ["journalctl", "--user", "--no-pager"]
        for container_name in containers:
            journal_args.extend(["-u", f"{container_name}.service"])
        if follow:
            journal_args.append("-f")
        if since is not None:
            journal_args.extend(["--since", str(since)])
        if tail is not None:
            journal_args.extend(["--lines", str(tail)])
        if until is not None:
            journal_args.extend(["--until", str(until)])
        _run_journalctl_json(
            journal_args,
            follow=follow,
            no_color=no_color,
            no_log_prefix=no_log_prefix,
            timestamps=timestamps,
        )
