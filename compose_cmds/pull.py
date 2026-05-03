"""compose_pull - Pull images for services defined in the compose file."""

from utils import resolve_compose_path, parse_compose, get_image_services, run_cmd


def compose_pull(
    compose_file: str | None = None, service: str | None = None, **_kwargs
) -> None:
    """Pull container images for services defined in the compose file.

    Uses `podman pull` for each service that specifies an image.
    """
    compose_path = resolve_compose_path(compose_file)
    compose_data = parse_compose(compose_path)
    services = get_image_services(compose_data)

    if not services:
        print("No services with images found.")
        return

    # Filter to a specific service if requested
    if service:
        if service not in services:
            raise ValueError(f"Service '{service}' not found in compose file.")
        services = {service: services[service]}

    for svc_name, image in services.items():
        print(f"Pulling image for service '{svc_name}': {image} ...")
        run_cmd(["podman", "pull", image])

    print("Done.")
