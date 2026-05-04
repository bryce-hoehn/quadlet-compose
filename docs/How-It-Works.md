# How It Works

1. **`up`** interpolates variables from `.env` and environment, injects a `name` field if missing, then runs `podlet --unit-directory --overwrite --absolute-host-paths compose --pod` to generate quadlet files. It reloads systemd, starts the pod, and follows logs by default (`-d` to detach). With `--kube`, it generates a `.kube` file instead.
2. **`down`** calls `systemctl --user stop` for the pod/kube service. With `--remove-files`, it also cleans up the generated quadlet files.
3. **`start`/`stop`/`restart`** detect the deployment mode (pod, kube, or plain) from existing quadlet files and call the corresponding `systemctl --user` commands on the appropriate target.
4. **`ps`** calls `systemctl --user status` on the pod/kube service or individual services.
5. **`logs`** calls `journalctl --user` for each service.
6. **`build`** parses the compose file for `build:` contexts and runs `podman build`.
7. **`pull`** parses the compose file for `image:` references and runs `podman pull`.
8. **`images`** and **`port`** parse the compose file directly — no subprocess calls.
9. **`top`** calls `podman stats` on the `systemd-<service>` containers.
10. **`config`** parses and validates the compose file, printing the normalized configuration.
11. **`convert`** runs `podlet compose` without `--unit-directory` to preview the generated quadlet files.

## Variable Interpolation

Before passing the compose file to `podlet`, podlet-compose resolves `$VAR` and `${VAR}` patterns using Python's `string.Template`. Variables are loaded from:

1. A `.env` file in the same directory as the compose file
2. Environment variables (take precedence over `.env`)

Unresolved variables are left as-is. Use `$$` for a literal `$`.

## Name Injection

`podlet compose --pod` requires a top-level `name:` field in the compose file. If missing, podlet-compose automatically injects the parent directory name as the project name.
