"""compose build command — build or rebuild services."""

from pathlib import Path

from rich.console import Console

from utils import run_cmd
from utils.compose import parse_compose, resolve_compose_path
from utils.mapping import map_compose
from utils.progress import track_operation
from utils.quadlet import get_unit_directory, run_quadlet_generator

HELP = "Build or rebuild services"
ARGS = [
    (
        "--build-arg",
        {"nargs": "*", "default": None, "help": "Set build-time variables"},
    ),
    ("--builder", {"default": None, "help": "Set builder to use"}),
    (
        "--check",
        {
            "action": "store_true",
            "default": False,
            "help": "Check build configuration",
        },
    ),
    (
        ("-m", "--memory"),
        {
            "default": None,
            "dest": "memory",
            "help": "Memory limit for build container",
        },
    ),
    (
        "--no-cache",
        {
            "action": "store_true",
            "default": False,
            "help": "Don't use cache when building",
        },
    ),
    (
        "--print",
        {
            "action": "store_true",
            "default": False,
            "help": "Print equivalent bake file",
        },
    ),
    (
        "--provenance",
        {
            "action": "store_true",
            "default": False,
            "help": "Add provenance attestation",
        },
    ),
    (
        "--pull",
        {
            "action": "store_true",
            "default": False,
            "help": "Always attempt to pull newer image",
        },
    ),
    (
        "--push",
        {
            "action": "store_true",
            "default": False,
            "help": "Push service images",
        },
    ),
    (
        ("-q", "--quiet"),
        {
            "action": "store_true",
            "default": False,
            "dest": "quiet",
            "help": "Suppress build output",
        },
    ),
    (
        "--sbom",
        {
            "action": "store_true",
            "default": False,
            "help": "Add SBOM attestation",
        },
    ),
    ("--ssh", {"default": None, "help": "SSH authentications for building"}),
    (
        "--with-dependencies",
        {
            "action": "store_true",
            "default": False,
            "help": "Also build dependencies",
        },
    ),
]


def compose_build(
    *,
    compose_file: str | None = None,
    build_arg: list[str] | None = None,
    builder: str | None = None,
    check: bool = False,
    memory: str | None = None,
    no_cache: bool = False,
    print: bool = False,
    provenance: bool = False,
    pull: bool = False,
    push: bool = False,
    quiet: bool = False,
    sbom: bool = False,
    ssh: str | None = None,
    with_dependencies: bool = False,
) -> None:
    """Build or rebuild services."""
    console = Console()
    compose_path = resolve_compose_path(compose_file)
    compose = parse_compose(compose_path)

    bundle = map_compose(compose, compose_path=compose_path)

    if not bundle.builds:
        console.print("[yellow]No services with build definitions found.[/yellow]")
        return

    # Write build unit files directly to the unit directory
    quadlet_files = bundle.to_quadlet_files()
    build_files = {k: v for k, v in quadlet_files.items() if k.endswith(".build")}
    unit_dir = get_unit_directory()
    for filename, content in build_files.items():
        dest = unit_dir / filename
        dest.write_text(content)

    # Run the Quadlet generator directly to produce .service files,
    # scoped to only this project's build files.
    run_quadlet_generator(unit_dir, files=list(build_files))

    # Reload systemd so it discovers the newly generated units
    run_cmd(["systemctl", "--user", "daemon-reload"])

    # Start build units
    build_services = [f'{unit.ImageTag or "build"}.service' for unit in bundle.builds]
    if quiet:
        for svc in build_services:
            run_cmd(["systemctl", "--user", "start", svc])
    else:
        track_operation(
            "Building",
            build_services,
            lambda svc: run_cmd(["systemctl", "--user", "start", svc]),
        )
