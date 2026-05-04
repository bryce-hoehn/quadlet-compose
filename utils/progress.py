"""Live progress display for compose commands (docker-compose-style output)."""

import itertools
import threading

from rich.console import Group
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
        Defaults to ``(kind, target)`` where kind is inferred from the target.
    """
    if not targets:
        return

    def _default_label(target):
        if target.endswith("-pod"):
            return "Pod", target[: -len("-pod")]
        return "Container", target

    _label = label_fn or _default_label

    results: dict[str, str] = {}  # target -> "ok" | "error"
    lock = threading.Lock()
    error_details: list[str] = []
    spinner_cycle = itertools.cycle(_SPINNERS)

    def worker():
        for target in targets:
            try:
                action_fn(target)
                with lock:
                    results[target] = "ok"
            except ComposeError as exc:
                with lock:
                    results[target] = "error"
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


def _build_frame(targets, results, spinner, action_label, label_fn) -> Group:
    """Build one frame of the progress display."""
    total = len(targets)
    completed = len(results)
    lines: list[Text] = [Text(f"[+] {action_label} {completed}/{total}")]
    for target in targets:
        kind, name = label_fn(target)
        if target in results:
            if results[target] == "ok":
                lines.append(Text(f" ✔ {kind} {name} {action_label}", style="green"))
            else:
                lines.append(Text(f" ✗ {kind} {name} Error", style="red"))
        else:
            lines.append(Text(f" {spinner} {kind} {name}"))
    return Group(*lines)
