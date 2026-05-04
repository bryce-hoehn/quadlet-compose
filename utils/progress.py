"""Live progress display for compose commands (docker-compose-style output)."""

import itertools
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
        *kind* is e.g. ``"Pod"`` or ``"Container"``, *name* is the display name.
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

    def worker():
        for target in targets:
            t0 = time.monotonic()
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

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()

    with Live(refresh_per_second=10, vertical_overflow="visible") as live:
        while thread.is_alive():
            live.update(
                _build_frame(
                    targets, results, next(spinner_cycle), action_label, _label
                )
            )
            thread.join(timeout=0.1)
        # Final frame (all completed)
        live.update(_build_frame(targets, results, " ", action_label, _label))

    if error_details:
        raise ComposeError("\n".join(error_details))


def _build_frame(targets, results, spinner, action_label, label_fn) -> Text:
    """Build one frame of the progress display as a single styled Text."""
    total = len(targets)
    completed = len(results)
    frame = Text()
    frame.append(f"[+] {action_label} {completed}/{total}\n")

    for target in targets:
        kind, name = label_fn(target)
        if target in results:
            status, elapsed = results[target]
            t = f"{elapsed:.1f}s"
            if status == "ok":
                frame.append(" ✔ ", style="green")
                frame.append(f"{kind} {name} ")
                frame.append(f"{action_label}", style="green")
                frame.append(f" {t}\n")
            else:
                frame.append(" ✗ ", style="red")
                frame.append(f"{kind} {name} ")
                frame.append("Error", style="red")
                frame.append(f" {t}\n")
        else:
            frame.append(f" {spinner} {kind} {name}\n")

    return frame
