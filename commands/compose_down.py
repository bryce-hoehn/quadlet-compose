"""compose down command — stop and remove containers."""

import subprocess
from pathlib import Path
from typing import Literal

from rich.console import Console

from utils.compose import parse_compose, resolve_compose_path
from utils.mapping import map_compose
from utils.quadlet import get_unit_directory

QUADLET_EXTENSIONS = frozenset(
    {".container", ".pod", ".network", ".volume", ".build"},
)
PROJECT_LABEL_PREFIX = "io.quadlet-compose.project="


def _find_project_files(
    unit_dir: Path,
    project_name: str,
) -> list[Path]:
    """Find all quadlet files in *unit_dir* belonging to *project_name*.

    A file belongs to a project when it contains the label
    ``io.quadlet-compose.project=<name>``.
    """
    label = f"{PROJECT_LABEL_PREFIX}{project_name}"
    files: list[Path] = []
    for path in unit_dir.iterdir():
        if not path.is_file() or path.suffix not in QUADLET_EXTENSIONS:
            continue
        if label in path.read_text():
            files.append(path)
    return files


def compose_down(
    *,
    compose_file: str | None = None,
    remove_orphans: bool = False,
    rmi: Literal["local", "all"] | None = None,
    timeout: int = 0,
    volumes: bool = False,
) -> None:
    """Stop containers."""
    console = Console()
    compose_path = resolve_compose_path(compose_file)
    compose = parse_compose(compose_path)

    bundle = map_compose(compose, compose_path=compose_path)
    quadlet_files = bundle.to_quadlet_files()

    unit_dir = get_unit_directory()

    # Stop orphaned services before daemon-reload
    if remove_orphans:
        current_filenames = set(quadlet_files)
        for path in _find_project_files(unit_dir, bundle.project_name):
            if path.name in current_filenames:
                continue
            stem, ext = path.name.rsplit(".", 1)
            svc = f"{stem}-{ext}.service"
            console.print(f"removing orphan {path.name}")
            subprocess.run(
                ["systemctl", "--user", "stop", svc],
                check=True,
            )
            path.unlink()

    subprocess.run(
        ["systemctl", "--user", "daemon-reload"],
        check=True,
    )

    # Disable any services that were enabled by restart policies
    for svc in bundle.restart_policies:
        console.print(f"disabling {svc}")
        subprocess.run(
            ["systemctl", "--user", "disable", svc],
            check=False,
        )

    # Stop all current services
    for svc in bundle.service_names():
        console.print(f"stopping {svc}")
        subprocess.run(
            ["systemctl", "--user", "stop", svc],
            check=True,
        )

    # Remove images if requested
    if rmi is not None:
        for unit in bundle.containers:
            image = unit.Image
            if not image:
                continue
            if rmi == "local" and ":" in image:
                # Only remove images that don't have a tag (local builds)
                continue
            console.print(f"removing image {image}")
            subprocess.run(
                ["podman", "rmi", image],
                check=False,
            )

    # Remove named volumes if requested
    if volumes:
        for unit in bundle.volumes:
            vol_name = unit.VolumeName
            if vol_name:
                console.print(f"removing volume {vol_name}")
                subprocess.run(
                    ["podman", "volume", "rm", vol_name],
                    check=False,
                )

    # Remove quadlet files
    for filename in quadlet_files:
        path = unit_dir / filename
        if path.exists():
            path.unlink()
            console.print(f"removed {path}")

    subprocess.run(
        ["systemctl", "--user", "daemon-reload"],
        check=True,
    )
