"""compose_top - Display resource usage for services."""

from utils import resolve_compose_path, parse_compose, run_cmd


def compose_top(compose_file: str | None = None, **_kwargs) -> None:
    """Display a live stream of container resource usage statistics.

    Runs podman stats scoped to the containers in this compose project.
    Container names are prefixed with 'systemd-' to match Quadlet's naming.
    """
    compose_path = resolve_compose_path(compose_file)
    compose_data = parse_compose(compose_path)
    service_names = compose_data["service_names"]

    if not service_names:
        print("No services defined in compose file.")
        return

    # Quadlet names containers systemd-<service> by default
    container_names = [f"systemd-{svc}" for svc in service_names]
    run_cmd(["podman", "stats", *container_names])
