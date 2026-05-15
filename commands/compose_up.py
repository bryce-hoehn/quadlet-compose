"""compose up command — create and start containers via quadlet."""

import subprocess
import tempfile
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


def compose_up(
    *,
    compose_file: str | None = None,
    detach: bool = False,
    remove_orphans: bool = False,
    build: bool = False,
    no_build: bool = False,
    quiet_build: bool = False,
    pull: Literal["always", "missing", "never"] | None = None,
    quiet_pull: bool = False,
    force_recreate: bool = False,
    no_recreate: bool = False,
    always_recreate_deps: bool = False,
    attach: list[str] | None = None,
    attach_dependencies: bool = False,
    no_attach: list[str] | None = None,
    no_color: bool = False,
    no_log_prefix: bool = False,
    timestamps: bool = False,
    abort_on_container_exit: bool = False,
    abort_on_container_failure: bool = False,
    exit_code_from: str | None = None,
    scale: list[str] | None = None,
    timeout: int | None = None,
    renew_anon_volumes: bool = False,
    wait: bool = False,
    wait_timeout: int | None = None,
    no_deps: bool = False,
    no_start: bool = False,
    menu: bool = False,
    watch: bool = False,
    yes: bool = False,
) -> None:
    """Create and start containers by writing quadlet files and starting systemd units."""
    console = Console()
    compose_path = resolve_compose_path(compose_file)
    compose = parse_compose(compose_path)

    bundle = map_compose(compose, compose_path=compose_path)
    quadlet_files = bundle.to_quadlet_files()

    unit_dir = get_unit_directory()

    # Stop orphaned services before installing new quadlet files
    if remove_orphans:
        current_filenames = set(quadlet_files)
        for path in _find_project_files(unit_dir, bundle.project_name):
            if path.name in current_filenames:
                continue
            # Quadlet → systemd: {stem}.{ext} → {stem}.service
            stem = path.name.rsplit(".", 1)[0]
            svc = f"{stem}.service"
            console.print(f"removing orphan {path.name}")
            subprocess.run(
                ["systemctl", "--user", "stop", svc],
                check=True,
            )
            path.unlink()

    # Write quadlet files to a temp dir, then install atomically via
    # `podman quadlet install` which handles copying + daemon-reload.
    with tempfile.TemporaryDirectory(prefix='quadlet-compose-') as tmp:
        tmp_dir = Path(tmp)
        for filename, content in quadlet_files.items():
            dest = tmp_dir / filename
            dest.write_text(content)
        subprocess.run(
            ['podman', 'quadlet', 'install', '--replace', str(tmp_dir)],
            check=True,
        )

    # Explicit daemon-reload to ensure the Quadlet generator has finished
    # converting .container/.pod/.network/.volume → .service units before
    # we try to start them.  `podman quadlet install` triggers reload via
    # D-Bus asynchronously, so this synchronous reload acts as a barrier.
    subprocess.run(
        ['systemctl', '--user', 'daemon-reload'],
        check=True,
    )

    # Start all current services
    for svc in bundle.service_names():
        console.print(f"starting {svc}")
        subprocess.run(
            ["systemctl", "--user", "start", svc],
            check=True,
        )

    # Enable services with restart: always / unless-stopped so they survive reboots
    for svc, policy in bundle.restart_policies.items():
        if policy in ("always", "unless-stopped"):
            console.print(f"enabling {svc} (restart: {policy})")
            subprocess.run(
                ["systemctl", "--user", "enable", svc],
                check=True,
            )
