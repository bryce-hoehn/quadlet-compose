"""compose_port - Print port bindings for services."""

from utils import resolve_compose_path, parse_compose


def compose_port(compose_file: str | None = None, **_kwargs) -> None:
    """Print the public port for a port binding.

    Parses the compose file's port mappings and displays them.
    """
    compose_path = resolve_compose_path(compose_file)
    compose_data = parse_compose(compose_path)
    services = compose_data["services"]

    found = False
    for svc_name, config in services.items():
        if not isinstance(config, dict):
            continue
        ports = config.get("ports", [])
        for port in ports:
            found = True
            if isinstance(port, str):
                print(f"{svc_name:<20}{port}")
            elif isinstance(port, dict):
                host = port.get("published", port.get("target", "?"))
                target = port.get("target", "?")
                protocol = port.get("protocol", "tcp")
                print(f"{svc_name:<20}{host}->{target}/{protocol}")

    if not found:
        print("No port bindings found.")
