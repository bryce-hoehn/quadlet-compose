"""compose convert command — preview quadlet files."""

import json
from typing import Literal

from rich.console import Console

from utils.compose import parse_compose, resolve_compose_path
from utils.mapping import map_compose

HELP = "Preview quadlet files"
ARGS = [
    (
        "--format",
        {
            "choices": ["yaml", "json"],
            "default": "yaml",
            "dest": "_format",
            "help": "Output format",
        },
    ),
    (
        "--hash",
        {
            "action": "store_true",
            "default": False,
            "help": "Print service config hash",
        },
    ),
    (
        "--images",
        {"action": "store_true", "default": False, "help": "Print image names"},
    ),
    (
        "--no-consistency",
        {
            "action": "store_true",
            "default": False,
            "help": "Don't check model consistency",
        },
    ),
    (
        "--no-interpolate",
        {
            "action": "store_true",
            "default": False,
            "help": "Don't interpolate environment variables",
        },
    ),
    (
        "--no-normalize",
        {
            "action": "store_true",
            "default": False,
            "help": "Don't normalize compose model",
        },
    ),
    (
        ("-o", "--output"),
        {"default": None, "dest": "output", "help": "Save to file"},
    ),
    (
        "--profiles",
        {
            "action": "store_true",
            "default": False,
            "help": "Print profile names",
        },
    ),
    (
        ("-q", "--quiet"),
        {
            "action": "store_true",
            "default": False,
            "dest": "quiet",
            "help": "Only validate, don't print",
        },
    ),
    (
        "--resolve-image-digests",
        {
            "action": "store_true",
            "default": False,
            "help": "Pin image tags to digests",
        },
    ),
    (
        "--services",
        {
            "action": "store_true",
            "default": False,
            "help": "Print service names",
        },
    ),
    (
        "--volumes",
        {
            "action": "store_true",
            "default": False,
            "help": "Print volume names",
        },
    ),
]


def compose_convert(
    *,
    compose_file: str | None = None,
    _format: Literal["yaml", "json"] = "yaml",
    hash: bool = False,
    images: bool = False,
    no_consistency: bool = False,
    no_interpolate: bool = False,
    no_normalize: bool = False,
    output: str | None = None,
    profiles: bool = False,
    quiet: bool = False,
    resolve_image_digests: bool = False,
    services: bool = False,
    volumes: bool = False,
) -> None:
    """Preview the generated quadlet files."""
    console = Console()
    compose_path = resolve_compose_path(compose_file)
    compose = parse_compose(compose_path, no_interpolate=no_interpolate)

    bundle = map_compose(compose, compose_path=compose_path)
    quadlet_files = bundle.to_quadlet_files()

    # --quiet: just validate silently
    if quiet:
        return

    # --images: list images used by services
    if images:
        for unit in bundle.containers:
            if unit.Image:
                console.print(unit.Image)
        return

    # --services: list systemd service names
    if services:
        for name in bundle.service_names():
            console.print(name)
        return

    # Default: output all quadlet files
    if _format == "json":
        console.print_json(json.dumps(quadlet_files, indent=2))
    else:
        for filename, content in sorted(quadlet_files.items()):
            console.print(f"\n# {filename}", style="bold")
            console.print(content)
