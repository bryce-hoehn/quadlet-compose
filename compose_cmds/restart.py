"""compose_restart - Restart all services defined in the compose file."""

from utils import resolve_compose_path, parse_compose, get_service_targets, run_cmd


def compose_restart(compose_file: str | None = None, **_kwargs) -> None:
    """Restart all systemd services defined in the compose file."""
    compose_path = resolve_compose_path(compose_file)
    compose_data = parse_compose(compose_path)

    if not compose_data["service_names"]:
        print("No services defined in compose file.")
        return

    targets = get_service_targets(compose_data)
    print(f"Restarting {', '.join(targets)} ...")
    run_cmd(["systemctl", "--user", "restart", *targets])
    print("Done.")
