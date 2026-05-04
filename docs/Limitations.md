# Limitations

## podlet-compose

- Variable interpolation only supports `$VAR` and `${VAR}` — default-value operators (`${VAR:-default}`, `${VAR-default}`, `${VAR:+alt}`, `${VAR+alt}`) are **not** supported.
- Some `podman compose` CLI options (e.g., `--env-file`, `--profile`) are not yet handled.
- Services always run as systemd user units — there is no system-level (root) mode (feature, not a bug!).
- Each compose file generates its own Podman pod. Containers in different pods **cannot share network namespaces** — `network_mode: "service:other-container"` only works when both services are in the **same** compose file (and therefore the same pod).
- Extension keys are not supported.
- Hostname / network_mode not supported.
- Depends_on conditions are not supported..

## Automatic workarounds applied

podlet-compose automatically applies the following transformations before passing the compose file to podlet:

| Transformation | Reason |
|---|---|
| Strip image tag when digest is present | Podlet cannot handle `image:repo:tag@sha256:digest` |
| Auto-expand single-value devices/ports/volumes | Podlet expects `host:container` format |
| Remove `x-*` extension keys | Podlet does not support compose extensions |
| Build images for `build:` services, replace with `image:` | Podlet cannot build images |
| Strip `hostname` and `network_mode` from services | Incompatible with shared pod UTS/network namespaces |
| Flatten long-form `depends_on` with conditions to short-form | Podlet cannot translate `condition: service_healthy` to systemd |
