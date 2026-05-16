"""Modern docker-compose-style TUI progress indication.

Displays one line per item with a Braille-spinner animation while
operations are in-progress, and right-aligned status with elapsed
time on completion::

    ⠋ Creating web.container
    ✔ Creating web.container                              done (0.0s)
    ⠋ Creating db.container
    ✔ Creating db.container                               done (0.1s)
"""

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

_ANSI_RE = re.compile(r"\033\[[0-9;]*m")


def _clear_line() -> str:
    return "\033[2K\r"


# ── Colour helpers ─────────────────────────────────────────────────────


def _green(s: str) -> str:
    return f"\033[32m{s}\033[0m"


def _red(s: str) -> str:
    return f"\033[31m{s}\033[0m"


def _yellow(s: str) -> str:
    return f"\033[33m{s}\033[0m"


_COLOR_FNS = {"green": _green, "red": _red, "yellow": _yellow}


def _colorize(text: str, color: str | None) -> str:
    fn = _COLOR_FNS.get(color) if color else None
    return fn(text) if fn else text


# ── Formatting helpers ─────────────────────────────────────────────────


def _visible_len(s: str) -> int:
    """Return the visible length of *s*, excluding ANSI escape codes."""
    return len(_ANSI_RE.sub("", s))


def _format_elapsed(seconds: float) -> str:
    """Format an elapsed duration for display."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins}m {secs}s"


def _status_icon(status: str, color: str | None) -> str:
    """Return a coloured icon for *status*."""
    icons = {"done": "✔", "error": "✗", "failed": "⚠"}
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

    Shows a Braille-spinner while each item is active, then replaces it
    with a right-aligned coloured status and elapsed time.

    Call :meth:`finish` (or use ``try/finally``) to stop the spinner
    thread.  It is a daemon thread so it won't prevent process exit,
    but ``finish`` avoids stale spinner output on error paths.
    """

    def __init__(self, stream: IO[str] | None = None) -> None:
        self._stream: IO[str] = stream or sys.stderr
        self._labels: list[str] = []
        self._start_times: dict[str, float] = {}
        self._lock = Lock()
        self._spinner_thread: Thread | None = None
        self._stop_event = Event()
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
        """Start progress display for all registered items."""
        if not self._labels:
            return
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

        if label not in self._labels:
            return

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

    Produces::

        ⠋ Starting web.service
        ✔ Starting web.service                              done (0.1s)
        ⠋ Starting db.service
        ✔ Starting db.service                               done (0.0s)
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
