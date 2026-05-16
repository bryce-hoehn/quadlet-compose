from .stop import compose_stop
from .start import compose_start

HELP = "Restart service containers (down + up)"
ARGS = [
    (
        "--no-deps",
        {
            "action": "store_true",
            "default": False,
            "help": "Don't restart dependent services",
        },
    ),
    (
        ("-t", "--timeout"),
        {
            "type": int,
            "default": 0,
            "dest": "timeout",
            "help": "Timeout in seconds",
        },
    ),
]


def compose_restart(
    *, compose_file: str | None = None, no_deps: bool = False, timeout: int = 0
) -> None:
    """Restart service containers (down + up)."""

    compose_stop(timeout=timeout)
    compose_start()
