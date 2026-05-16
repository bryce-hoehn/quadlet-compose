"""compose config command — validate and view compose config."""

import json
from typing import Literal

from rich.console import Console

from utils.compose import parse_compose, resolve_compose_path

HELP = "Validate and view compose config"
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
        "--environment",
        {
            "action": "store_true",
            "default": False,
            "help": "Print environment used for interpolation",
        },
    ),
    ("--hash", {"default": None, "help": "Print service config hash"}),
    (
        "--images",
        {"action": "store_true", "default": False, "help": "Print image names"},
    ),
    (
        "--lock-image-digests",
        {
            "action": "store_true",
            "default": False,
            "help": "Produce override with image digests",
        },
    ),
    (
        "--models",
        {"action": "store_true", "default": False, "help": "Print model names"},
    ),
    (
        "--networks",
        {
            "action": "store_true",
            "default": False,
            "help": "Print network names",
        },
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
        "--no-env-resolution",
        {
            "action": "store_true",
            "default": False,
            "help": "Don't resolve env files",
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
        "--no-path-resolution",
        {
            "action": "store_true",
            "default": False,
            "help": "Don't resolve file paths",
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
        "--variables",
        {
            "action": "store_true",
            "default": False,
            "help": "Print model variables",
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


def compose_config(
    *,
    compose_file: str | None = None,
    _format: Literal["yaml", "json"] = "yaml",
    environment: bool = False,
    hash: str | None = None,
    images: bool = False,
    lock_image_digests: bool = False,
    models: bool = False,
    networks: bool = False,
    no_consistency: bool = False,
    no_env_resolution: bool = False,
    no_interpolate: bool = False,
    no_normalize: bool = False,
    no_path_resolution: bool = False,
    output: str | None = None,
    profiles: bool = False,
    quiet: bool = False,
    resolve_image_digests: bool = False,
    services: bool = False,
    variables: bool = False,
    volumes: bool = False,
) -> None:
    """Validate and view the compose file configuration."""
    console = Console()
    compose_path = resolve_compose_path(compose_file)

    # Parse and validate — will raise on invalid compose
    data = parse_compose(compose_path, no_interpolate=no_interpolate)

    # --services: list service names
    if services:
        for name in sorted(data.get("services", {}).keys()):
            console.print(name)
        return

    # --volumes: list volume names
    if volumes:
        for name in sorted(data.get("volumes", {}).keys()):
            console.print(name)
        return

    # --networks: list network names
    if networks:
        for name in sorted(data.get("networks", {}).keys()):
            console.print(name)
        return

    # --images: list images used by services
    if images:
        svc_data = data.get("services", {})
        image_names = sorted(
            {
                s["image"]
                for s in svc_data.values()
                if isinstance(s, dict) and "image" in s
            }
        )
        for name in image_names:
            console.print(name)
        return

    # --quiet: just validate silently
    if quiet:
        return

    # Default: output the full config
    if _format == "json":
        console.print_json(json.dumps(data, indent=2))
    else:
        console.print(data)
