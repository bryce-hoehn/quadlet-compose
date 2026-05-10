"""compose_down - Stop services defined in compose.yaml."""

from utils import (
    resolve_compose_path,
    parse_compose,
    get_service_targets,
    run_cmd,
)
from utils.progress import run_with_progress


def compose_down(compose_file: str | None = None, **_kwargs) -> None:
    """Stop systemd services for the compose project.

    Stops the pod/kube service (which stops all containers).  Quadlet files
    are left in place so containers remain inspectable with ``podman logs``
    after stopping.
    """
    compose_path = resolve_compose_path(compose_file)
    compose_data = parse_compose(compose_path)
    service_names = compose_data["service_names"]

    if not service_names:
        return

    targets = get_service_targets(compose_data)

    def stop_target(target):
        run_cmd(["systemctl", "--user", "stop", target])

    run_with_progress(targets, stop_target, "Stopped")
