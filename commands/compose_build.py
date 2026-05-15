"""compose build command — build or rebuild services."""

import subprocess

from rich.console import Console

from utils.compose import parse_compose, resolve_compose_path
from utils.mapping import map_compose
from utils.quadlet import get_unit_directory


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

    unit_dir = get_unit_directory()

    # Write build unit files
    quadlet_files = bundle.to_quadlet_files()
    build_files = {k: v for k, v in quadlet_files.items() if k.endswith(".build")}
    for filename, content in build_files.items():
        dest = unit_dir / filename
        dest.write_text(content)
        if not quiet:
            console.print(f"  wrote {dest}")

    subprocess.run(
        ["systemctl", "--user", "daemon-reload"],
        check=True,
    )

    # Start build units
    for unit in bundle.builds:
        tag = unit.ImageTag or "build"
        svc = f"{tag}-build.service"
        if not quiet:
            console.print(f"building {svc}")
        subprocess.run(
            ["systemctl", "--user", "start", svc],
            check=True,
        )
