"""compose_start - Start services."""

from utils import resolve_compose_path, parse_compose, get_service_targets, run_cmd


def compose_start(compose_file: str | None = None, **_kwargs) -> None:
    """Start services defined in the compose file without regenerating quadlets."""
    compose_path = resolve_compose_path(compose_file)
    compose_data = parse_compose(compose_path)

    if not compose_data["service_names"]:
        print("No services defined in compose file.")
        return

    targets = get_service_targets(compose_data)
    print(f"Starting {', '.join(targets)} ...")
    run_cmd(["systemctl", "--user", "start", *targets])
    print("Done.")
