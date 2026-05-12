"""compose_down - Stop services defined in compose.yaml."""

from utils import (
    resolve_compose_path,
    parse_compose,
    get_service_targets,
    get_unit_directory,
    run_cmd,
)
from utils.progress import run_with_progress


def compose_down(
    compose_file: str | None = None,
    remove_orphans: bool = False,
    **_kwargs,
) -> None:
    """Stop systemd services for the compose project.

    Stops the pod/kube service (which stops all containers).  Quadlet files
    are left in place so containers remain inspectable with ``podman logs``
    after stopping.

    Set *remove_orphans* to True to also remove quadlet files for services
    no longer defined in the compose file, then remove the pod.
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

    if remove_orphans:
        _remove_orphans(compose_data)


def _remove_orphans(compose_data: dict) -> None:
    """Remove quadlet files and pod for services no longer in the compose file."""
    from compose_cmds.up import _remove_stale_files

    project = compose_data["project"]
    unit_dir = get_unit_directory()

    removed = _remove_stale_files(
        unit_dir,
        project,
        compose_data["service_names"],
        compose_data["volume_names"],
        compose_data["network_names"],
    )

    run_cmd(
        ["podman", "pod", "rm", "--force", project],
        quiet=True,
    )
