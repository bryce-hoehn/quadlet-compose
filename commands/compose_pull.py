"""compose pull command — pull service images."""

import subprocess

from rich.console import Console
from typing import Literal
from utils.compose import parse_compose, resolve_compose_path
from utils.mapping import map_compose


def compose_pull(
    *,
    compose_file: str | None = None,
    ignore_buildable: bool = False,
    ignore_pull_failures: bool = False,
    include_deps: bool = False,
    policy: Literal["missing", "always"] | None = None,
    quiet: bool = False,
) -> None:
    """Pull service images."""
    console = Console()
    compose_path = resolve_compose_path(compose_file)
    compose = parse_compose(compose_path)

    bundle = map_compose(compose, compose_path=compose_path)

    images = []
    for unit in bundle.containers:
        if unit.Image:
            # Skip buildable images if requested
            if ignore_buildable:
                # Check if any build unit produces this image
                is_buildable = any(b.ImageTag == unit.Image for b in bundle.builds)
                if is_buildable:
                    continue
            images.append(unit.Image)

    if not images:
        if not quiet:
            console.print("[yellow]No images to pull.[/yellow]")
        return

    for image in images:
        if not quiet:
            console.print(f"pulling {image}")

        args = ["podman", "pull"]

        if quiet:
            args.append("--quiet")

        args.append(image)

        result = subprocess.run(args, check=False)
        if result.returncode != 0 and not ignore_pull_failures:
            raise RuntimeError(f"Failed to pull {image}")
