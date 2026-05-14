"""compose up command — create and start containers via quadlet."""

import subprocess
from pathlib import Path

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


def compose_up(
    *,
    compose_file: str | None = None,
    kube: bool = False,
    detach: bool = False,
    remove_orphans: bool = False,
) -> None:
    """Create and start containers by writing quadlet files and starting systemd units."""
    console = Console()
    compose_path = resolve_compose_path(compose_file)
    compose = parse_compose(compose_path)

    bundle = map_compose(compose, compose_path=compose_path)
    quadlet_files = bundle.to_quadlet_files()

    unit_dir = get_unit_directory()

    # Write quadlet files
    for filename, content in quadlet_files.items():
        dest = unit_dir / filename
        dest.write_text(content)
        console.print(f"  wrote {dest}")

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

    # Start all current services
    for svc in bundle.service_names():
        console.print(f"starting {svc}")
        subprocess.run(
            ["systemctl", "--user", "start", svc],
            check=True,
        )
