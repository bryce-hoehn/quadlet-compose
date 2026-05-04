# Limitations

## podlet-compose

- Variable interpolation only supports `$VAR` and `${VAR}` — default-value operators (`${VAR:-default}`, `${VAR-default}`, `${VAR:+alt}`, `${VAR+alt}`) are **not** supported.
- Some `podman compose` CLI options (e.g., `--env-file`, `--profile`) are not yet handled.
- Services always run as systemd user units — there is no system-level (root) mode.

## Inherited from [podlet](https://github.com/containers/podlet)

- `build:` in compose files is not supported and will produce an error.
- Not all compose file options are supported; unsupported options cause errors.
- A top-level `name:` field is required when using `--pod` or `--kube` mode (podlet-compose auto-injects the directory name if missing).
- Relative host paths in Kubernetes YAML files are not modified when using `--pod`.
- Only host paths in standard Quadlet options (not `PodmanArgs=`) are resolved to absolute paths.
