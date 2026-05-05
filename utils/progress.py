"""Live progress display for compose commands (docker-compose-style output)."""

import itertools
import shutil
import threading
import time

from rich.live import Live
from rich.text import Text

from .utils import ComposeError

_SPINNERS = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]


def run_with_progress(
    targets: list[str],
    action_fn,
    action_label: str,
    label_fn=None,
) -> None:
    """Run *action_fn* for each target with a live-updating progress display.

    Parameters
    ----------
    targets:
        Ordered list of target names to process.
    action_fn:
        Callable ``(target: str) -> None``.  Raise ``ComposeError`` on failure.
    action_label:
        Past-tense verb for completed items (e.g. ``"Started"``).
    label_fn:
        Optional callable ``(target: str) -> (kind, name)`` for display.
    """
    if not targets:
        return

    def _default_label(target):
        if target.endswith("-pod"):
            return "Pod", target[: -len("-pod")]
        return "Container", target

    _label = label_fn or _default_label

    # results: target -> ("ok" | "error", elapsed_seconds)
    results: dict[str, tuple[str, float]] = {}
    lock = threading.Lock()
    error_details: list[str] = []
    spinner_cycle = itertools.cycle(_SPINNERS)
    current_target: list[str | None] = [None]
    start_times: dict[str, float] = {}

    def worker():
        for target in targets:
            with lock:
                current_target[0] = target
                start_times[target] = time.monotonic()
            t0 = start_times[target]
            try:
                action_fn(target)
                elapsed = time.monotonic() - t0
                with lock:
                    results[target] = ("ok", elapsed)
            except ComposeError as exc:
                elapsed = time.monotonic() - t0
                with lock:
                    results[target] = ("error", elapsed)
                    error_details.append(str(exc))
        with lock:
            current_target[0] = None

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()

    fps = 15
    with Live(refresh_per_second=fps, vertical_overflow="visible") as live:
        while thread.is_alive():
            now = time.monotonic()
            live.update(
                _build_frame(
                    targets,
                    results,
                    next(spinner_cycle),
                    action_label,
                    _label,
                    start_times,
                    now,
                )
            )
            thread.join(timeout=1 / fps)
        # Final frame
        live.update(
            _build_frame(
                targets,
                results,
                " ",
                action_label,
                _label,
                start_times,
                time.monotonic(),
            )
        )

    if error_details:
        raise ComposeError("\n".join(error_details))


def _build_frame(
    targets, results, spinner, action_label, label_fn, start_times, now
) -> Text:
    """Build one frame of the progress display as a single styled Text."""
    term_width = shutil.get_terminal_size().columns
    total = len(targets)
    completed = len(results)
    frame = Text()
    frame.append(f"[+] {action_label} {completed}/{total}\n")

    for target in targets:
        kind, name = label_fn(target)
        if target in results:
            status, elapsed = results[target]
            t = f"{elapsed:.1f}s"
            line_start = f" ✔ {kind} {name} "
            line_end = f" {t}"
            status_word = action_label
            visible_len = len(line_start) + len(status_word) + len(line_end)
            padding = max(1, term_width - visible_len - 1)
            if status == "ok":
                frame.append(line_start)
                frame.append(status_word, style="green")
                frame.append(" " * padding)
                frame.append(f"{t}\n")
            else:
                frame.append(line_start.replace("✔", "✗"))
                frame.append("Error", style="red")
                frame.append(" " * padding)
                frame.append(f"{t}\n")
        else:
            line_start = f" {spinner} {kind} {name}"
            t0 = start_times.get(target)
            if t0 is not None:
                elapsed = now - t0
                t = f" {elapsed:.1f}s"
                padding = max(1, term_width - len(line_start) - len(t) - 1)
                frame.append(line_start)
                frame.append(" " * padding)
                frame.append(f"{t}\n")
            else:
                frame.append(f"{line_start}\n")

    return frame
