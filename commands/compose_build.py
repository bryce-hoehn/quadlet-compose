"""compose build command — build or rebuild services."""

import subprocess
import tempfile
from pathlib import Path

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

    # Write build unit files to a temp dir, then install atomically via
    # `podman quadlet install` which handles the generator + daemon-reload.
    quadlet_files = bundle.to_quadlet_files()
    build_files = {k: v for k, v in quadlet_files.items() if k.endswith(".build")}
    with tempfile.TemporaryDirectory(prefix='quadlet-compose-') as tmp:
        tmp_dir = Path(tmp)
        for filename, content in build_files.items():
            dest = tmp_dir / filename
            dest.write_text(content)
        subprocess.run(
            ["podman", "quadlet", "install", "--replace", str(tmp_dir)],
            check=True,
        )

    # Start build units
    for unit in bundle.builds:
        tag = unit.ImageTag or "build"
        # Quadlet: {tag}.build → {tag}.service
        svc = f"{tag}.service"
        if not quiet:
            console.print(f"building {svc}")
        subprocess.run(
            ["systemctl", "--user", "start", svc],
            check=True,
        )
