"""compose_up - Generate quadlet files from compose.yaml and start services."""

import subprocess

from utils import (
    get_unit_directory,
    resolve_compose_path,
    prepare_compose,
    parse_compose,
    run_cmd,
)


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

    # Ensure compose file has a `name` field (required by podlet --pod/--kube)
    podlet_input = prepare_compose(compose_path)

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
    cmd.append(str(podlet_input))

    # Generate quadlet files
    print(f"Generating quadlet files in {unit_dir} ...")
    result = run_cmd(cmd)
    if result.stdout:
        print(result.stdout, end="")

    # Reload systemd to pick up new unit files
    print("Reloading systemd daemon ...")
    run_cmd(["systemctl", "--user", "daemon-reload"])

    # Start the appropriate service targets
    if kube:
        targets = [project]
    else:
        # In pod mode, start the pod first, then each container service.
        # The pod service only creates the infra container; individual
        # .container units must be started separately.
        targets = [f"{project}-pod"] + [
            f"{project}-{svc}" for svc in compose_data["service_names"]
        ]

    for target in targets:
        print(f"Starting {target} ...")
        run_cmd(["systemctl", "--user", "start", target])

    if detach:
        print("Done.")
    else:
        # Follow container logs via podman (Ctrl+C to stop)
        print("Following logs (Ctrl+C to stop) ...")
        # In pod mode, container names are systemd-{project}-{service}
        # In kube mode, use the pod name
        if kube:
            container_names = [f"systemd-{project}"]
        else:
            container_names = [
                f"systemd-{project}-{svc}" for svc in compose_data["service_names"]
            ]
        podman_args = ["podman", "logs", "-f"] + container_names
        try:
            subprocess.run(podman_args)
        except KeyboardInterrupt:
            print("\nDetached from logs. Services are still running.")
