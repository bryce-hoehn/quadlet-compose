# Limitations

## podlet-compose

- Variable interpolation only supports `$VAR` and `${VAR}` — default-value operators (`${VAR:-default}`, `${VAR-default}`, `${VAR:+alt}`, `${VAR+alt}`) are **not** supported.
- Some `podman compose` CLI options (e.g., `--env-file`, `--profile`) are not yet handled.
- Services always run as systemd user units — there is no system-level (root) mode (feature, not a bug!).
- Each compose file generates its own Podman pod. Containers in different pods **cannot share network namespaces** — `network_mode: "service:other-container"` only works when both services are in the **same** compose file (and therefore the same pod).

## Inherited from [podlet](https://github.com/containers/podlet)

- Not all compose file options are supported; unsupported options cause errors.
- A top-level `name:` field is required when using `--pod` or `--kube` mode (podlet-compose auto-injects the directory name if missing).
- Relative host paths in Kubernetes YAML files are not modified when using `--pod`.
- Only host paths in standard Quadlet options (not `PodmanArgs=`) are resolved to absolute paths.
- `configs` and non-external `secrets` are not supported.
- `depends_on` with `condition: service_healthy` or `condition: service_completed_successfully` is not supported.
- `depends_on` with `restart: true` and `required: false` is not supported.

## Automatic workarounds applied

podlet-compose automatically applies the following transformations before passing the compose file to podlet:

| Transformation | Reason |
|---|---|
| Strip image tag when digest is present | Podlet cannot handle `image:repo:tag@sha256:digest` |
| Auto-expand single-value devices/ports/volumes | Podlet expects `host:container` format |
| Remove `x-*` extension keys | Podlet does not support compose extensions |
| Strip `hostname` and `network_mode` from services | Incompatible with shared pod UTS/network namespaces |
| Fix unsupported `depends_on` conditions, preserve `required`/`restart` | Podlet errors on `service_healthy`/`service_completed_successfully` conditions |
| Strip `configs` and non-external `secrets` | Podlet does not support `configs` and only supports external secrets |
