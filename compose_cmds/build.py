"""compose_build - Build images for services with build contexts."""

from utils import resolve_compose_path, parse_compose, get_build_services, run_cmd


def compose_build(compose_file: str | None = None, **_kwargs) -> None:
    """Build images for services that define a build context in the compose file.

    Uses `podman build` for each service with a build context.
    """
    compose_path = resolve_compose_path(compose_file)
    compose_data = parse_compose(compose_path)
    services = get_build_services(compose_data)

    if not services:
        print("No services with build contexts found.")
        return

    for svc_name, build_ctx in services.items():
        context = build_ctx.get("context", ".")
        dockerfile = build_ctx.get("dockerfile", None)
        tag = (
            build_ctx.get("tags", [f"{svc_name}:latest"])[0]
            if build_ctx.get("tags")
            else f"{svc_name}:latest"
        )

        cmd = ["podman", "build", "-t", tag]
        if dockerfile:
            cmd += ["-f", dockerfile]
        cmd.append(context)

        print(f"Building image for service '{svc_name}' ...")
        run_cmd(cmd)

    print("Done.")
