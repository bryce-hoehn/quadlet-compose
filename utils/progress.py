"""Docker-compose v1-style TUI progress indication.

Ported from ``compose.parallel.ParallelStreamWriter`` and
``compose.progress_stream`` in docker-compose v1.

Each operation gets its own terminal line.  ANSI escape codes move the
cursor to the correct line so that statuses can be updated in-place::

    Creating web ...
    Creating db ...
    Creating redis ...

When an operation finishes the line is overwritten::

    Creating web ... done
    Creating db ...
    Creating redis ... done
"""

from __future__ import annotations

import sys
from threading import Lock
from typing import IO, Callable

from rich.console import Console
from rich.text import Text

# ── ANSI helpers (same codes used by docker-compose v1) ──────────────

ESC = "\033["


def _move_up(n: int) -> str:
    return f"{ESC}{n}A"


def _move_down(n: int) -> str:
    return f"{ESC}{n}B"


def _clear_line() -> str:
    return f"{ESC}2K\r"


# ── Colour helpers ───────────────────────────────────────────────────


def _green(s: str) -> str:
    return f"\033[32m{s}\033[0m"


def _red(s: str) -> str:
    return f"\033[31m{s}\033[0m"


def _yellow(s: str) -> str:
    return f"\033[33m{s}\033[0m"


# ── ProgressWriter ───────────────────────────────────────────────────


class ProgressWriter:
    """Write status lines that are updated in-place, matching the
    docker-compose v1 visual style.

    Usage::

        writer = ProgressWriter()
        writer.add('Creating', 'web')
        writer.add('Creating', 'db')
        writer.write_initial()

        # ... do work ...

        writer.update('Creating', 'web', 'done', color='green')
        writer.update('Creating', 'db', 'error', color='red')

    When *stream* is not a TTY the writer falls back to simple
    line-by-line output (no cursor movement).
    """

    def __init__(self, stream: IO[str] | None = None) -> None:
        self._stream: IO[str] = stream or sys.stderr
        self._is_tty: bool = hasattr(self._stream, "isatty") and self._stream.isatty()
        self._lines: list[str] = []  # e.g. "Creating web"
        self._width: int = 0
        self._lock = Lock()

    # ── registration ─────────────────────────────────────────────

    def add(self, msg: str, obj: str) -> None:
        """Register an object that will get its own progress line."""
        label = f"{msg} {obj}"
        self._lines.append(label)
        self._width = max(self._width, len(label))

    # ── output ───────────────────────────────────────────────────

    def write_initial(self) -> None:
        """Print all registered lines with a trailing ``...`` (empty status)."""
        for label in self._lines:
            self._write_line(label, "")

    def update(
        self,
        msg: str,
        obj: str,
        status: str,
        *,
        color: str | None = None,
    ) -> None:
        """Overwrite the line for *msg obj* with *status*.

        *color* is one of ``'green'``, ``'red'``, ``'yellow'`` (or *None*
        for no colour).
        """
        label = f"{msg} {obj}"
        colored = _colorize(status, color)

        if self._is_tty and label in self._lines:
            self._update_ansi(label, colored)
        else:
            # Non-TTY: just print a new line
            self._write_noansi(label, colored)

    # ── ANSI path (TTY) ─────────────────────────────────────────

    def _update_ansi(self, label: str, status: str) -> None:
        with self._lock:
            pos = self._lines.index(label)
            diff = len(self._lines) - pos
            self._stream.write(_move_up(diff))
            self._stream.write(_clear_line())
            self._stream.write(f"{label:<{self._width}} ... {status}\r")
            self._stream.write(_move_down(diff))
            self._stream.flush()

    # ── plain-text path (non-TTY / pipe) ─────────────────────────

    def _write_noansi(self, label: str, status: str) -> None:
        with self._lock:
            self._stream.write(f"{label:<{self._width}} ... {status}\n")
            self._stream.flush()

    def _write_line(self, label: str, status: str) -> None:
        self._write_noansi(label, status)


# ── Convenience: sequential operation progress ───────────────────────


def track_operation(
    msg: str,
    items: list[str],
    func: Callable[[str], None],
    *,
    stream: IO[str] | None = None,
) -> None:
    """Run *func* on each item while showing docker-compose v1-style progress.

    Example::

        track_operation(
            'Starting',
            ['web.service', 'db.service'],
            lambda svc: run_cmd(['systemctl', '--user', 'start', svc]),
        )

    Produces::

        Starting web.service ... done
        Starting db.service ... done
    """
    writer = ProgressWriter(stream)
    for item in items:
        writer.add(msg, item)
    writer.write_initial()

    for item in items:
        try:
            func(item)
            writer.update(msg, item, "done", color="green")
        except Exception:
            writer.update(msg, item, "error", color="red")
            raise


# ── helpers ──────────────────────────────────────────────────────────


def _colorize(text: str, color: str | None) -> str:
    if color == "green":
        return _green(text)
    if color == "red":
        return _red(text)
    if color == "yellow":
        return _yellow(text)
    return text
