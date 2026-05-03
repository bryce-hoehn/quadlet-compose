"""compose_images - List images used by services."""

from utils import resolve_compose_path, parse_compose, get_image_services


def compose_images(compose_file: str | None = None, **_kwargs) -> None:
    """List images used by the services defined in the compose file."""
    compose_path = resolve_compose_path(compose_file)
    compose_data = parse_compose(compose_path)
    image_services = get_image_services(compose_data)

    if not image_services:
        print("No services with images found.")
        return

    print(f"{'SERVICE':<20}{'IMAGE'}")
    for svc_name, image in image_services.items():
        print(f"{svc_name:<20}{image}")
