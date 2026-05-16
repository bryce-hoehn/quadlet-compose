"""Modern docker-compose-style TUI progress indication.

Displays one line per item with a Braille-spinner animation while
operations are in-progress, and right-aligned status with elapsed
time on completion.

TTY output (in-place spinner → final status)::

    ⠋ Creating web.container
    ✔ Creating web.container                              done (0.0s)
    ⠋ Creating db.container
    ✔ Creating db.container                               done (0.1s)

Non-TTY output (pipes, redirects)::

    Creating web.container ... done (0.0s)
    Creating db.container ... done (0.1s)
"""

from __future__ import annotations

import re
import shutil
import sys
import time
from threading import Event, Lock, Thread
from typing import IO, Callable

# ── Spinner frames (Braille patterns) ─────────────────────────────────

_SPINNER_FRAMES = ("⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏")
_SPINNER_INTERVAL = 0.08  # ~12 fps

# ── ANSI helpers ───────────────────────────────────────────────────────

ESC = "\033["


def _clear_line() -> str:
    return f"{ESC}2K\r"


# ── Colour helpers ─────────────────────────────────────────────────────


def _green(s: str) -> str:
    return f"\033[32m{s}\033[0m"


def _red(s: str) -> str:
    return f"\033[31m{s}\033[0m"


def _yellow(s: str) -> str:
    return f"\033[33m{s}\033[0m"


def _colorize(text: str, color: str | None) -> str:
    if color == "green":
        return _green(text)
    if color == "red":
        return _red(text)
    if color == "yellow":
        return _yellow(text)
    return text


# ── Formatting helpers ─────────────────────────────────────────────────


def _visible_len(s: str) -> int:
    """Return the visible length of *s*, excluding ANSI escape codes."""
    return len(re.sub(r"\033\[[0-9;]*m", "", s))


def _format_elapsed(seconds: float) -> str:
    """Format an elapsed duration for display."""
    if seconds < 0:
        seconds = 0.0
    if seconds < 60:
        return f"{seconds:.1f}s"
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins}m {secs}s"


def _status_icon(status: str, color: str | None) -> str:
    """Return a coloured icon for *status*."""
    icons = {"done": "✔", "error": "✗", "Error": "✗", "failed": "⚠"}
    icon = icons.get(status, "•")
    return _colorize(icon, color) if color else icon


# ── ProgressWriter ─────────────────────────────────────────────────────


class ProgressWriter:
    """Write progress lines with spinner animation and right-aligned status.

    Usage::

        writer = ProgressWriter()
        writer.add('Creating', 'web')
        writer.add('Creating', 'db')
        writer.write_initial()

        # ... do work ...

        writer.update('Creating', 'web', 'done', color='green')
        writer.update('Creating', 'db', 'error', color='red')
        writer.finish()

    On TTY streams, shows a Braille-spinner while each item is active,
    then replaces it with a right-aligned coloured status and elapsed
    time.  On non-TTY streams, prints one completion line per item.

    Call :meth:`finish` (or use ``try/finally``) to stop the spinner
    thread.  It is a daemon thread so it won't prevent process exit,
    but ``finish`` avoids stale spinner output on error paths.
    """

    def __init__(self, stream: IO[str] | None = None) -> None:
        self._stream: IO[str] = stream or sys.stderr
        self._is_tty: bool = hasattr(self._stream, "isatty") and self._stream.isatty()
        self._labels: list[str] = []
        self._start_times: dict[str, float] = {}
        self._lock = Lock()
        self._spinner_thread: Thread | None = None
        self._stop_event = Event()
        self._term_width = 80
        if self._is_tty:
            try:
                self._term_width = shutil.get_terminal_size().columns or 80
            except (ValueError, OSError):
                self._term_width = 80

    # ── registration ─────────────────────────────────────────────

    def add(self, msg: str, obj: str) -> None:
        """Register an item that will get its own progress line."""
        label = f"{msg} {obj}"
        self._labels.append(label)

    # ── output ───────────────────────────────────────────────────

    def write_initial(self) -> None:
        """Start progress display for all registered items.

        On a TTY this starts the spinner on the first item.  On a
        non-TTY this is a no-op (completion lines are printed by
        :meth:`update`).
        """
        if not self._labels:
            return
        if self._is_tty:
            self._start_times[self._labels[0]] = time.monotonic()
            self._start_spinner(self._labels[0])

    def update(
        self,
        msg: str,
        obj: str,
        status: str,
        *,
        color: str | None = None,
    ) -> None:
        """Update the line for *msg obj* with *status*.

        *color* is one of ``'green'``, ``'red'``, ``'yellow'``
        (or *None* for no colour).
        """
        label = f"{msg} {obj}"
        elapsed = (
            time.monotonic() - self._start_times[label]
            if label in self._start_times
            else 0.0
        )

        if self._is_tty and label in self._labels:
            self._stop_spinner()
            with self._lock:
                icon = _status_icon(status, color)
                status_colored = _colorize(status, color)
                elapsed_str = _format_elapsed(elapsed)
                right = f"{icon} {status_colored} {elapsed_str}"
                right_vis = _visible_len(right)
                padding = max(2, self._term_width - len(label) - right_vis)
                self._stream.write(_clear_line())
                self._stream.write(f'{label}{" " * padding}{right}\n')
                self._stream.flush()

            # Advance to the next item
            idx = self._labels.index(label)
            if idx + 1 < len(self._labels):
                next_label = self._labels[idx + 1]
                self._start_times[next_label] = time.monotonic()
                self._start_spinner(next_label)
        else:
            # Non-TTY or unknown label — plain line
            self._write_plain(label, status, color, elapsed)

    def finish(self) -> None:
        """Stop the spinner thread if still running."""
        self._stop_spinner()

    # ── Spinner ──────────────────────────────────────────────────

    def _start_spinner(self, label: str) -> None:
        self._stop_event.clear()
        self._spinner_thread = Thread(
            target=self._spin,
            args=(label,),
            daemon=True,
        )
        self._spinner_thread.start()

    def _stop_spinner(self) -> None:
        if self._spinner_thread is not None:
            self._stop_event.set()
            self._spinner_thread.join()
            self._spinner_thread = None

    def _spin(self, label: str) -> None:
        i = 0
        while not self._stop_event.is_set():
            frame = _SPINNER_FRAMES[i % len(_SPINNER_FRAMES)]
            with self._lock:
                self._stream.write(_clear_line())
                self._stream.write(f"{frame} {label}\r")
                self._stream.flush()
            i += 1
            self._stop_event.wait(_SPINNER_INTERVAL)

    # ── Plain-text path (non-TTY / pipe / unknown label) ─────────

    def _write_plain(
        self,
        label: str,
        status: str,
        color: str | None,
        elapsed: float,
    ) -> None:
        with self._lock:
            elapsed_str = _format_elapsed(elapsed)
            status_colored = _colorize(status, color)
            self._stream.write(f"{label} ... {status_colored} {elapsed_str}\n")
            self._stream.flush()


# ── Convenience: sequential operation progress ────────────────────────


def track_operation(
    msg: str,
    items: list[str],
    func: Callable[[str], None],
    *,
    stream: IO[str] | None = None,
) -> None:
    """Run *func* on each item while showing progress.

    Example::

        track_operation(
            'Starting',
            ['web.service', 'db.service'],
            lambda svc: run_cmd(['systemctl', '--user', 'start', svc]),
        )

    Produces (TTY)::

        ⠋ Starting web.service
        ✔ Starting web.service                              done (0.1s)
        ⠋ Starting db.service
        ✔ Starting db.service                               done (0.0s)

    Produces (non-TTY)::

        Starting web.service ... done (0.1s)
        Starting db.service ... done (0.0s)
    """
    writer = ProgressWriter(stream)
    for item in items:
        writer.add(msg, item)
    writer.write_initial()

    try:
        for item in items:
            try:
                func(item)
                writer.update(msg, item, "done", color="green")
            except Exception:
                writer.update(msg, item, "error", color="red")
                raise
    finally:
        writer.finish()
