"""compose up command — create and start containers via quadlet."""

from pathlib import Path
from typing import Literal

from rich.console import Console

from utils import run_cmd
from utils.compose import parse_compose, resolve_compose_path
from utils.mapping import map_compose
from utils.progress import track_operation
from utils.quadlet import get_unit_directory, run_quadlet_generator

HELP = "Create and start containers"
ARGS = [
    (
        ("-d", "--detach"),
        {
            "action": "store_true",
            "default": False,
            "help": "Run in background without following logs",
        },
    ),
    (
        "--remove-orphans",
        {
            "action": "store_true",
            "default": False,
            "help": "Remove containers for services not defined in the Compose file",
        },
    ),
    (
        "--build",
        {
            "action": "store_true",
            "default": False,
            "help": "Build images before starting containers",
        },
    ),
    (
        "--no-build",
        {
            "action": "store_true",
            "default": False,
            "help": "Don't build an image, even if policy",
        },
    ),
    (
        "--quiet-build",
        {
            "action": "store_true",
            "default": False,
            "help": "Suppress build output",
        },
    ),
    (
        "--pull",
        {
            "choices": ["always", "missing", "never"],
            "default": None,
            "help": "Pull image before running",
        },
    ),
    (
        "--quiet-pull",
        {
            "action": "store_true",
            "default": False,
            "help": "Pull without printing progress",
        },
    ),
    (
        "--force-recreate",
        {
            "action": "store_true",
            "default": False,
            "help": "Recreate even if config unchanged",
        },
    ),
    (
        "--no-recreate",
        {
            "action": "store_true",
            "default": False,
            "help": "Don't recreate existing containers",
        },
    ),
    (
        "--always-recreate-deps",
        {
            "action": "store_true",
            "default": False,
            "help": "Recreate dependent containers",
        },
    ),
    (
        "--attach",
        {
            "nargs": "*",
            "default": None,
            "help": "Restrict attaching to specified services",
        },
    ),
    (
        "--attach-dependencies",
        {
            "action": "store_true",
            "default": False,
            "help": "Attach to log output of dependent services",
        },
    ),
    (
        "--no-attach",
        {
            "nargs": "*",
            "default": None,
            "help": "Don't attach to specified services",
        },
    ),
    (
        "--no-color",
        {
            "action": "store_true",
            "default": False,
            "help": "Produce monochrome output",
        },
    ),
    (
        "--no-log-prefix",
        {
            "action": "store_true",
            "default": False,
            "help": "Don't print prefix in logs",
        },
    ),
    (
        "--timestamps",
        {"action": "store_true", "default": False, "help": "Show timestamps"},
    ),
    (
        "--abort-on-container-exit",
        {
            "action": "store_true",
            "default": False,
            "help": "Stop all if any container stops",
        },
    ),
    (
        "--abort-on-container-failure",
        {
            "action": "store_true",
            "default": False,
            "help": "Stop all if any container fails",
        },
    ),
    (
        "--exit-code-from",
        {"default": None, "help": "Return exit code of selected service"},
    ),
    (
        "--scale",
        {
            "nargs": "*",
            "default": None,
            "help": "Scale SERVICE to NUM instances",
        },
    ),
    (
        ("-t", "--timeout"),
        {
            "type": int,
            "default": None,
            "dest": "timeout",
            "help": "Timeout in seconds for container shutdown",
        },
    ),
    (
        ("-V", "--renew-anon-volumes"),
        {
            "action": "store_true",
            "default": False,
            "dest": "renew_anon_volumes",
            "help": "Recreate anonymous volumes",
        },
    ),
    (
        "--wait",
        {
            "action": "store_true",
            "default": False,
            "help": "Wait for services to be running|healthy",
        },
    ),
    (
        "--wait-timeout",
        {
            "type": int,
            "default": None,
            "help": "Max duration to wait for services",
        },
    ),
    (
        "--no-deps",
        {
            "action": "store_true",
            "default": False,
            "help": "Don't start linked services",
        },
    ),
    (
        "--no-start",
        {
            "action": "store_true",
            "default": False,
            "help": "Don't start services after creating",
        },
    ),
    (
        "--menu",
        {
            "action": "store_true",
            "default": False,
            "help": "Enable interactive shortcuts",
        },
    ),
    (
        ("-w", "--watch"),
        {
            "action": "store_true",
            "default": False,
            "dest": "watch",
            "help": "Watch source code and rebuild on change",
        },
    ),
    (
        ("-y", "--yes"),
        {
            "action": "store_true",
            "default": False,
            "dest": "yes",
            "help": "Assume yes to all prompts",
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
            run_cmd(["systemctl", "--user", "stop", svc])
            path.unlink()

    # Write quadlet files directly to the unit directory
    track_operation(
        "Creating",
        list(quadlet_files.keys()),
        lambda f: (unit_dir / f).write_text(quadlet_files[f]),
    )

    # Run the Quadlet generator directly to produce .service files,
    # scoped to only this project's quadlet files.
    run_quadlet_generator(unit_dir, files=list(quadlet_files))

    # Reload systemd so it discovers the newly generated units
    run_cmd(["systemctl", "--user", "daemon-reload"])

    # Start all current services
    track_operation(
        "Starting",
        list(bundle.service_names()),
        lambda svc: run_cmd(["systemctl", "--user", "start", svc]),
    )
