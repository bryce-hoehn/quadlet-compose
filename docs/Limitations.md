# Limitations

## quadlet-compose

- Some `podman compose` CLI options (e.g., `--env-file`, `--profile`) are not yet handled.
- Services always run as systemd user units — there is no system-level (root) mode (feature, not a bug!).
- Each compose file generates its own Podman pod. Containers in different pods **cannot share network namespaces** — `network_mode: "service:other-container"` only works when both services are in the **same** compose file (and therefore the same pod).
- A top-level `name:` field is required when using `--pod` or `--kube` mode (enable the `name_inject` hack to auto-inject the directory name).
- `configs` and non-external `secrets` are not supported.
- `depends_on` with `condition: service_healthy` or `condition: service_completed_successfully` is not supported.
- `depends_on` with `restart: true` and `required: false` is not supported.

## Optional workarounds

quadlet-compose provides optional hacks (disabled by default) to work around many of these limitations. See the [Hacks](Hacks) page for details.

| Hack | Workaround |
|---|---|
| `interpolate` | Resolve variables from `.env` and environment before passing to podlet |
| `name_inject` | Auto-inject `name:` from directory if missing |
| `normalize` | Strip image tags with digests, remove `hostname`/`network_mode`, fix `depends_on`, strip `configs`/non-external `secrets` |
| `expand` | Expand single-value devices, ports, and volumes to `host:container` format |
| `strip_extensions` | Remove `x-*` compose extension keys |
