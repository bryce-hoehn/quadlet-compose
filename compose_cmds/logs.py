"""compose_logs - Show logs from services."""

from utils import resolve_compose_path, parse_compose, get_service_targets, run_cmd


def compose_logs(
    compose_file: str | None = None, service: str | None = None, **_kwargs
) -> None:
    """Show logs from services defined in the compose file.

    If a specific service is given, show logs for that service only.
    Otherwise, show logs for all services.
    """
    compose_path = resolve_compose_path(compose_file)
    compose_data = parse_compose(compose_path)
    service_names = compose_data["service_names"]

    if not service_names:
        print("No services defined in compose file.")
        return

    if service:
        if service not in service_names:
            raise ValueError(f"Service '{service}' not found in compose file.")
        targets = [service]
    else:
        targets = get_service_targets(compose_data)

    # journalctl requires --unit per target
    cmd = ["journalctl", "--user"]
    for t in targets:
        cmd.extend(["--unit", t])
    run_cmd(cmd)
