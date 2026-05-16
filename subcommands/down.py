"""compose down command — stop and remove containers."""

import subprocess
from pathlib import Path
from typing import Literal

from rich.console import Console

from utils import run_cmd
from utils.compose import parse_compose, resolve_compose_path
from utils.mapping import map_compose
from utils.progress import track_operation
from utils.quadlet import get_unit_directory

HELP = "Stop and remove containers"
ARGS = [
    (
        "--remove-orphans",
        {
            "action": "store_true",
            "default": False,
            "help": "Remove containers for services not defined in the Compose file",
        },
    ),
    (
        "--rmi",
        {"choices": ["local", "all"], "default": None, "help": "Remove images"},
    ),
    (
        ("-t", "--timeout"),
        {
            "type": int,
            "default": 0,
            "dest": "timeout",
            "help": "Timeout in seconds for container shutdown",
        },
    ),
    (
        ("-v", "--volumes"),
        {
            "action": "store_true",
            "default": False,
            "dest": "volumes",
            "help": "Remove named volumes declared as external",
        },
    ),
]

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
            # Quadlet → systemd: {stem}.{ext} → {stem}.service
            stem = path.name.rsplit(".", 1)[0]
            svc = f"{stem}.service"
            console.print(f"removing orphan {path.name}")
            run_cmd(["systemctl", "--user", "stop", svc])
            path.unlink()

    run_cmd(["systemctl", "--user", "daemon-reload"])

    # Stop all current services
    track_operation(
        "Stopping",
        list(bundle.service_names()),
        lambda svc: run_cmd(["systemctl", "--user", "stop", svc]),
    )

    # Remove images if requested
    if rmi is not None:
        images = [
            unit.Image
            for unit in bundle.containers
            if unit.Image and not (rmi == "local" and ":" in unit.Image)
        ]
        track_operation(
            "Removing image",
            images,
            lambda img: subprocess.run(["podman", "rmi", img], check=False),
        )

    # Remove named volumes if requested
    if volumes:
        vol_names = [unit.VolumeName for unit in bundle.volumes if unit.VolumeName]
        track_operation(
            "Removing volume",
            vol_names,
            lambda vol: subprocess.run(
                ["podman", "volume", "rm", vol],
                check=False,
            ),
        )

    # Remove quadlet files
    track_operation(
        "Removing",
        list(quadlet_files.keys()),
        lambda f: (unit_dir / f).unlink() if (unit_dir / f).exists() else None,
    )

    run_cmd(["systemctl", "--user", "daemon-reload"])
