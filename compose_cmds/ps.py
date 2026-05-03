"""compose_ps - Show status of containers."""

from utils import resolve_compose_path, parse_compose, get_service_targets, run_cmd


def compose_ps(compose_file: str | None = None, **_kwargs) -> None:
    """Show the status of services defined in the compose file."""
    compose_path = resolve_compose_path(compose_file)
    compose_data = parse_compose(compose_path)

    if not compose_data["service_names"]:
        print("No services defined in compose file.")
        return

    targets = get_service_targets(compose_data)
    run_cmd(["systemctl", "--user", "status", *targets])
