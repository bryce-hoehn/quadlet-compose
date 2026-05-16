"""compose pull command — pull service images."""

import subprocess

from rich.console import Console
from typing import Literal
from utils import run_cmd
from utils.compose import parse_compose, resolve_compose_path
from utils.mapping import map_compose
from utils.progress import ProgressWriter

HELP = "Pull service images"
ARGS = [
    (
        "--ignore-buildable",
        {
            "action": "store_true",
            "default": False,
            "help": "Skip images that can be built",
        },
    ),
    (
        "--ignore-pull-failures",
        {
            "action": "store_true",
            "default": False,
            "help": "Continue on pull failure",
        },
    ),
    (
        "--include-deps",
        {
            "action": "store_true",
            "default": False,
            "help": "Also pull dependencies",
        },
    ),
    (
        "--policy",
        {
            "choices": ["missing", "always"],
            "default": None,
            "help": "Pull policy",
        },
    ),
    (
        ("-q", "--quiet"),
        {
            "action": "store_true",
            "default": False,
            "dest": "quiet",
            "help": "Suppress output",
        },
    ),
]


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

    writer = ProgressWriter()
    for image in images:
        writer.add("Pulling", image)
    writer.write_initial()

    try:
        for image in images:
            args = ["podman", "pull"]
            if quiet:
                args.append("--quiet")
            args.append(image)

            result = subprocess.run(args, check=False)
            if result.returncode != 0:
                if ignore_pull_failures:
                    writer.update("Pulling", image, "failed", color="yellow")
                else:
                    writer.update("Pulling", image, "error", color="red")
                    raise RuntimeError(f"Failed to pull {image}")
            else:
                writer.update("Pulling", image, "done", color="green")
    finally:
        writer.finish()
