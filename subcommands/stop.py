"""compose stop command — stop containers without disabling them."""

from utils import run_cmd
from utils.compose import parse_compose, resolve_compose_path
from utils.mapping import map_compose
from utils.progress import track_operation

HELP = "Stop containers without disabling them"
ARGS = [
    (
        ("-t", "--timeout"),
        {
            "type": int,
            "default": None,
            "dest": "timeout",
            "help": "Timeout in seconds for container shutdown",
        },
    ),
]


def compose_stop(
    *,
    compose_file: str | None = None,
    timeout: int | None = None,
) -> None:
    """Stop containers without disabling systemd units.

    Unlike ``compose_down``, this does **not** disable or remove units.
    Use ``compose_start`` to resume.
    """
    compose_path = resolve_compose_path(compose_file)
    compose = parse_compose(compose_path)

    bundle = map_compose(compose, compose_path=compose_path)

    def _stop_svc(svc: str) -> None:
        cmd = ["systemctl", "--user", "stop", svc]
        if timeout is not None:
            cmd.extend(["--job-mode", "replace-irreversibly"])
        run_cmd(cmd)

    track_operation(
        "Stopping",
        list(bundle.service_names()),
        _stop_svc,
    )
