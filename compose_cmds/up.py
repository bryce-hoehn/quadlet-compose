"""compose_up - Generate quadlet files from compose.yaml and start services."""

import subprocess

from utils import get_unit_directory, resolve_compose_path, parse_compose, run_cmd


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
    compose_path = resolve_compose_path(compose_file)
    compose_data = parse_compose(compose_path)
    project = compose_data["project"]
    unit_dir = get_unit_directory()

    # Build podlet command with docker-compose-compatible defaults
    # podlet options and must precede the "compose" subcommand.
    cmd = [
        "podlet",
        "--unit-directory",
        "--overwrite",
        "--absolute-host-paths",
        "compose",
    ]
    if kube:
        cmd.append("--kube")
    else:
        cmd.append("--pod")
    cmd.append(str(compose_path))

    # Generate quadlet files
    print(f"Generating quadlet files in {unit_dir} ...")
    result = run_cmd(cmd)
    if result.stdout:
        print(result.stdout, end="")

    # Reload systemd to pick up new unit files
    print("Reloading systemd daemon ...")
    run_cmd(["systemctl", "--user", "daemon-reload"])

    # Start the appropriate service target
    if kube:
        target = project
    else:
        target = f"{project}-pod"
    print(f"Starting {target} ...")
    run_cmd(["systemctl", "--user", "start", target])

    if detach:
        print("Done.")
    else:
        # Follow logs in attached mode (Ctrl+C to stop)
        print(f"Following logs for {target} (Ctrl+C to stop) ...")
        try:
            subprocess.run(["journalctl", "--user", "-u", target, "-f"])
        except KeyboardInterrupt:
            print("\nDetached from logs. Services are still running.")
