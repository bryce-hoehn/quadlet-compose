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


def _ensure_bind_mount_dirs(compose_data: dict, compose_dir: Path) -> None:
    """Create host directories for bind mounts that don't yet exist.

    Scans all service volumes and creates missing host paths.
    Named volumes (without a path separator) are skipped.
    """
    for svc_config in compose_data["services"].values():
        if not isinstance(svc_config, dict):
            continue
        for vol in svc_config.get("volumes", []):
            # Volume can be a string ("host:container[:mode]") or a dict
            host_spec = vol if isinstance(vol, str) else vol.get("source", "")
            if not host_spec:
                continue
            # Split on ':' — host path is the first part
            parts = host_spec.split(":")
            raw_host = parts[0]
            # Skip named volumes (no path separator and doesn't start with . or /)
            if "/" not in raw_host and not raw_host.startswith("."):
                continue
            # Resolve relative paths against the compose file directory
            host_path = (compose_dir / raw_host).resolve()
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
        "--install",
        "--wanted-by",
        "default.target",
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

    # Generate quadlet files (suppress podlet's stdout)
    run_cmd(cmd, quiet=True)

    # Reload systemd to pick up new unit files
    run_cmd(["systemctl", "--user", "daemon-reload"], quiet=True)

    # Determine targets
    if kube:
        targets = [project]
    else:
        # In pod mode, start the pod first, then each container service.
        # The pod service only creates the infra container; individual
        # .container units must be started separately.
        targets = [f"{project}-pod"] + [
            f"{project}-{svc}" for svc in compose_data["service_names"]
        ]

    # Enable autostart for services with a non-"no" restart policy.
    # All units already have [Install] sections from --install --wanted-by.
    _AUTOSTART_POLICIES = {"always", "unless-stopped", "on-failure"}
    enable_targets: list[str] = []
    if not kube:
        for svc_name, svc_config in compose_data["services"].items():
            if not isinstance(svc_config, dict):
                continue
            restart = svc_config.get("restart", "no")
            if restart in _AUTOSTART_POLICIES:
                enable_targets.append(f"{project}-{svc_name}")

    # Reload systemd to pick up new unit files (with [Install] sections)
    run_cmd(["systemctl", "--user", "daemon-reload"], quiet=True)

    if enable_targets:
        run_cmd(["systemctl", "--user", "enable", *enable_targets], quiet=True)

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
