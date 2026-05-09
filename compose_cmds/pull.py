"""compose_pull - Pull images for services defined in the compose file."""

from utils import resolve_compose_path, parse_compose, get_image_services, run_cmd
from utils.progress import run_with_progress


def compose_pull(compose_file: str | None = None, **_kwargs) -> None:
    """Pull container images for services defined in the compose file.

    Uses `podman pull` for each service that specifies an image.
    """
    compose_path = resolve_compose_path(compose_file)
    compose_data = parse_compose(compose_path)
    services = get_image_services(compose_data)

    if not services:
        return

    targets = list(services.keys())
    images = services  # name -> image ref

    def pull_target(svc_name):
        run_cmd(["podman", "pull", images[svc_name]], quiet=True)

    def label(svc_name):
        return "Image", images[svc_name]

    run_with_progress(targets, pull_target, "Pulled", label_fn=label)
