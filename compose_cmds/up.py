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
    """True if the source looks like a host path (not a named volume)."""
    return source.startswith(".") or source.startswith("/")


def _parse_volume_host_path(vol) -> str | None:
    """Extract the host-side path from a volume entry, or None if not a bind mount.

    Handles both short-form strings and long-form dicts per the Compose spec:

      - ``"host:container[:mode]"``          → host path if bind mount
      - ``{type: bind, source: ./data, …}``  → source
      - ``{type: volume, source: data, …}``  → None (named volume)
    """
    if isinstance(vol, str):
        source = vol.split(":")[0]
        return source if _is_bind_mount(source) else None

    if isinstance(vol, dict):
        vol_type = vol.get("type")
        source = vol.get("source", "")
        if vol_type == "bind":
            return source
        # Fallback: no explicit type but source looks like a path
        if vol_type is None and _is_bind_mount(source):
            return source
        return None

    return None


def _ensure_bind_mount_dirs(compose_data: dict, compose_dir: Path) -> None:
    """Create host directories for bind mounts that don't yet exist."""
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


def compose_up(
    compose_file: str | None = None,
    kube: bool = False,
    detach: bool = False,
    **_kwargs,
) -> None:
    """Generate Podman Quadlet files from a compose file and start the services.

    Uses `podlet compose` with --pod (default) or --kube mode, plus
    --overwrite and --absolute-host-paths for docker-compose-compatible
    behavior. Then reloads systemd and starts the services.

    By default, follows service logs with journalctl (attached mode).
    Use -d/--detach to start without following logs.
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

    # ensure directory gets created
    get_unit_directory()
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

    # Create host directories for bind mounts (docker-compose compatibility)
    _ensure_bind_mount_dirs(compose_data, compose_path.parent.resolve())

    # Generate quadlet files with [Install] sections (suppress podlet's stdout).
    # The Quadlet systemd generator reads [Install] and creates .wants/
    # symlinks automatically
    run_cmd(cmd, quiet=True)

    # Explicitly generate .service files from quadlet unit files.
    # The systemd Quadlet generator should do this during daemon-reload,
    # but it may not trigger in all environments (e.g. CI).  Running
    # podman quadlet directly is more reliable and harmless when the
    # generator has already run.
    run_cmd(["podman", "quadlet"], quiet=True)

    # Reload systemd — picks up the newly generated .service files.
    run_cmd(["systemctl", "--user", "daemon-reload"], quiet=True)

    # Determine targets
    if kube:
        targets = [project]
    else:
        # In pod mode, starting the pod automatically starts all containers
        # via Quadlet's StartWithPod=true (default). No need to start
        # individual container units separately.
        targets = [f"{project}-pod"]

    # Start targets with live progress display
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
