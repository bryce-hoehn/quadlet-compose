"""compose_stop - Stop services."""

from utils import resolve_compose_path, parse_compose, get_service_targets, run_cmd


def compose_stop(compose_file: str | None = None, **_kwargs) -> None:
    """Stop services defined in the compose file without removing them."""
    compose_path = resolve_compose_path(compose_file)
    compose_data = parse_compose(compose_path)

    if not compose_data["service_names"]:
        print("No services defined in compose file.")
        return

    targets = get_service_targets(compose_data)
    print(f"Stopping {', '.join(targets)} ...")
    run_cmd(["systemctl", "--user", "stop", *targets])
    print("Done.")
