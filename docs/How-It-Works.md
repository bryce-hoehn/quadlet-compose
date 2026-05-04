# How It Works

1. **`up`** runs `podlet --unit-directory --overwrite --skip-services-check --install --wanted-by default.target --absolute-host-paths compose --pod` to generate quadlet files from the compose file. It reloads systemd, enables autostart for services with restart policies, starts the pod (containers start automatically via Quadlet's `StartWithPod=true`), and follows logs by default (`-d` to detach). With `--kube`, it generates a `.kube` file instead.
2. **`down`** calls `systemctl --user stop` for the pod/kube service. With `--remove-files`, it also cleans up the generated quadlet files.
3. **`restart`** runs `down` then `up` — stops services, regenerates quadlet files, and starts everything fresh.
4. **`ps`** calls `systemctl --user status` on the pod/kube service or individual services.
5. **`logs`** calls `journalctl --user` for each service.
6. **`build`** parses the compose file for `build:` contexts and runs `podman build`.
7. **`pull`** parses the compose file for `image:` references and runs `podman pull`.
8. **`images`** and **`port`** parse the compose file directly — no subprocess calls.
9. **`top`** calls `podman stats` on the `systemd-<service>` containers.
10. **`config`** parses and validates the compose file, printing the normalized configuration.
11. **`convert`** runs `podlet compose` without `--unit-directory` to preview the generated quadlet files.

## Non-Destructive Processing (Temp File)

podlet-compose **never modifies your source compose file**. All transformations are applied to a temporary copy:

1. The original `compose.yaml` is read into memory
2. Enabled text-level hacks are applied (e.g. variable interpolation)
3. The text is parsed with `ruamel.yaml`
4. Enabled dict-level hacks are applied to the in-memory data
5. The result is written to a **temporary file** (`tempfile.NamedTemporaryFile`)
6. `podlet compose` processes the temp file instead of the original

This ensures your source files remain untouched regardless of what transformations are needed.

## Hacks (Optional Workarounds)

All compose file transformations are **disabled by default** and controlled via the `PODLET_COMPOSE_HACKS` environment variable. See the [Hacks](Hacks) page for full details.

Available hacks:

| Hack | Description |
|---|---|
| `interpolate` | Resolve `$VAR` / `${VAR}` / `${VAR:-default}` from `.env` and environment |
| `name_inject` | Inject `name:` from parent directory if missing |
| `normalize` | Strip/fix fields podlet cannot handle |
| `expand` | Expand single-value devices, ports, and volumes |
| `strip_extensions` | Remove `x-*` compose extension keys |

> **Note:** `build:` is now handled natively by podlet v0.3.1+ which generates `.build` Quadlet files. No pre-build step is needed.
