"""compose_up - Generate quadlet files from compose.yaml and start services."""

import getpass
import os
import subprocess
from pathlib import Path

from rich.console import Console

from utils import (
    ComposeError,
    get_unit_directory,
    resolve_compose_path,
    prepare_compose,
    parse_compose,
    run_cmd,
)
from utils.progress import run_with_progress

_console = Console()


def _is_bind_mount(source: str) -> bool:
    return source.startswith(".") or source.startswith("/")


def _parse_volume_host_path(vol) -> str | None:
    if isinstance(vol, str):
        source = vol.split(":")[0]
        return source if _is_bind_mount(source) else None

    if isinstance(vol, dict):
        vol_type = vol.get("type")
        source = vol.get("source", "")
        if vol_type == "bind":
            return source
        if vol_type is None and _is_bind_mount(source):
            return source
        return None

    return None


def _ensure_bind_mount_dirs(compose_data: dict, compose_dir: Path) -> None:
    for svc_config in compose_data["services"].values():
        if not isinstance(svc_config, dict):
            continue
        for vol in svc_config.get("volumes", []):
            host_path_str = _parse_volume_host_path(vol)
            if host_path_str is None:
                continue
            host_path = (compose_dir / host_path_str).resolve()
            if not host_path.exists():
                os.makedirs(host_path, exist_ok=True)


def _remove_stale_files(
    unit_dir: Path,
    project: str,
    current_services: list[str],
    current_volumes: list[str],
    current_networks: list[str],
) -> list[str]:
    """Remove quadlet files and containers for services no longer in compose.

    For ``.container`` / ``.build`` files the corresponding podman container
    is force-removed so the pod will not restart it on the next ``up``.

    Returns a list of removed file names.
    """
    current_bases = {f"{project}-{svc}" for svc in current_services}
    current_bases.update(f"{project}-{v}" for v in current_volumes)
    current_bases.update(f"{project}-{n}" for n in current_networks)
    current_bases.add(f"{project}-pod")
    current_bases.add(f"{project}.pod")
    current_bases.add(f"{project}.kube")
    current_bases.add(f"{project}-kube")

    stale = []
    for f in unit_dir.iterdir():
        if not f.name.startswith(f"{project}-"):
            continue
        stem = f.stem
        if stem in current_bases:
            continue
        if any(stem == f"{project}-{svc}" for svc in current_services):
            continue
        if f.suffix in (".container", ".build", ".volume", ".network", ".pod", ".kube"):
            stale.append(f)
        elif f.name.endswith("-kube.yaml"):
            stale.append(f)

    for f in stale:
        _console.print(f'Removing orphan container "{f.stem}"')
        try:
            run_cmd(["systemctl", "--user", "stop", f.stem], quiet=True)
        except ComposeError:
            pass
        if f.suffix in (".container", ".build"):
            try:
                run_cmd(["podman", "rm", "--force", f.stem], quiet=True)
            except ComposeError:
                pass
        f.unlink()

    return [f.name for f in stale]


def compose_up(
    compose_file: str | None = None,
    kube: bool = False,
    detach: bool = False,
    remove_orphans: bool = False,
    **_kwargs,
) -> None:
    """Generate Podman Quadlet files from a compose file and start the services.

    Uses `podlet compose` with --pod (default) or --kube mode, plus
    --overwrite and --absolute-host-paths for docker-compose-compatible
    behavior. Then reloads systemd and starts the services.

    By default, follows service logs with journalctl (attached mode).
    Use -d/--detach to start without following logs.

    Set *remove_orphans* to True to remove quadlet files for services
    that are no longer defined in the compose file.
    """

    try:
        linger_path = Path(f"/var/lib/systemd/linger/{getpass.getuser()}")
        if not linger_path.exists():
            _console.print(
                "[yellow]⚠[/yellow] Lingering is not enabled. "
                "Services will not autostart on boot.\n"
                "  Fix: [cyan]loginctl enable-linger[/cyan]\n"
            )
    except Exception:
        pass  # Non-critical check, don't block on failure

    compose_path = resolve_compose_path(compose_file)
    compose_data = parse_compose(compose_path)
    project = compose_data["project"]

    # Ensure compose file has a `name` field (required by podlet --pod/--kube)
    podlet_input = prepare_compose(compose_path)

    # Build podlet command with docker-compose-compatible defaults
    # podlet options and must precede the "compose" subcommand.
    # Pass the original compose directory to --absolute-host-paths so
    # relative paths resolve correctly (not from the temp file's location).
    compose_dir = str(compose_path.parent.resolve())

    unit_dir = get_unit_directory()

    if remove_orphans:
        removed = _remove_stale_files(
            unit_dir,
            project,
            compose_data["service_names"],
            compose_data["volume_names"],
            compose_data["network_names"],
        )

    cmd = [
        "podlet",
        "--unit-directory",
        "--overwrite",
        "--skip-services-check",
        # "--install",
        # "--wanted-by",
        # "default.target",
        f"--absolute-host-paths={compose_dir}",
        "compose",
    ]
    if kube:
        cmd.append("--kube")
    else:
        cmd.append("--pod")
    cmd.append(str(podlet_input))

    # Create host directories for bind mounts
    _ensure_bind_mount_dirs(compose_data, compose_path.parent.resolve())

    run_cmd(cmd, quiet=True)

    run_cmd(["systemctl", "--user", "daemon-reload"], quiet=True)

    # Determine targets
    if kube:
        targets = [project]
    else:
        targets = [f"{project}-pod"]

    def start_target(target):
        run_cmd(["systemctl", "--user", "start", target])

    run_with_progress(targets, start_target, "Started")

    if not detach:
        # Follow container logs via podman (Ctrl+C to stop)
        # Use podman ps to discover actual container names in the pod
        if kube:
            container_names = [project]
        else:
            try:
                ps_result = run_cmd(
                    [
                        "podman",
                        "ps",
                        "--filter",
                        f"pod={project}",
                        "--format",
                        "{{.Names}}",
                    ],
                    quiet=True,
                )
                # Filter out the infra container
                container_names = [
                    n
                    for n in (ps_result.stdout or "").splitlines()
                    if n and "-infra" not in n
                ]
            except ComposeError:
                container_names = list(compose_data["service_names"])

        if container_names:
            podman_args = ["podman", "logs", "-f"] + container_names
            try:
                subprocess.run(podman_args)
            except KeyboardInterrupt:
                _console.print("\nDetached from logs. Services are still running.")
