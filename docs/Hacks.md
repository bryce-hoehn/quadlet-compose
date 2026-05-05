# Hacks (Podlet Workarounds)

podlet-compose includes optional workarounds for known podlet limitations and compose file transformations. **All hacks are disabled by default** — your compose file is passed to podlet as-is.

Enable hacks via the `PODLET_COMPOSE_HACKS` environment variable:

```bash
# Enable specific hacks
PODLET_COMPOSE_HACKS=interpolate,name_inject podlet-compose up

# Enable all hacks
PODLET_COMPOSE_HACKS=all podlet-compose up

# No hacks (default)
podlet-compose up
```

## Available Hacks

### `interpolate`

Resolves `$VAR`, `${VAR}`, and Docker-style default-value patterns from `.env` and environment variables:

| Pattern | Behavior |
|---|---|
| `$VAR` / `${VAR}` | Substitute variable (empty string if unset) |
| `${VAR:-default}` | Use *default* if VAR is unset **or empty** |
| `${VAR-default}` | Use *default* if VAR is unset |
| `${VAR:+alt}` | Use *alt* if VAR is set and non-empty |
| `${VAR+alt}` | Use *alt* if VAR is set (even if empty) |
| `$$` | Literal `$` escape |

Variables are loaded from a `.env` file next to the compose file, with environment variables taking precedence.

### `name_inject`

Injects a top-level `name:` field from the compose file's parent directory name if missing. This is required by `podlet compose --pod` / `--kube` mode.

### `normalize`

Strips or transforms compose fields that podlet cannot handle:

| Transformation | Reason |
|---|---|
| Strip image tag when digest is present | Podlet rejects `image:repo:tag@sha256:digest` |
| Strip `hostname` and `network_mode` | Incompatible with shared pod namespaces |
| Fix unsupported `depends_on` conditions | Podlet errors on `condition: service_healthy` / `service_completed_successfully`; preserves `required` and `restart` flags |
| Strip `configs` | Podlet does not support compose `configs` |
| Strip non-external `secrets` | Podlet only supports external secrets |

### `expand`

Auto-expands single-value entries that docker-compose allows but podlet does not:

| Transformation | Example |
|---|---|
| Expand single-value devices | `["/dev/dri"]` → `["/dev/dri:/dev/dri"]` |
| Expand single-value ports | `["8080"]` → `["8080:8080"]` |
| Expand path-like single volumes | `["./data"]` → `["./data:./data"]` |

Named volumes (e.g. `["data"]`) are left unchanged.

### `strip_extensions`

Removes all top-level `x-*` extension keys from the compose file. Podlet does not support compose extensions (e.g. `x-custom`, `x-env`).

## When to Enable Hacks

- Enable `interpolate` if your compose file uses `$VAR` / `${VAR}` patterns that need resolution before podlet processes the file.
- Enable `name_inject` if your compose file lacks a `name:` field and you're using `--pod` or `--kube` mode.
- Enable `normalize` if your compose file uses `hostname`, `network_mode`, `configs`, non-external `secrets`, image tags with digests, or `depends_on` with `service_healthy`/`service_completed_successfully` conditions.
- Enable `expand` if your compose file uses short-form devices, ports, or volumes.
- Enable `strip_extensions` if your compose file contains `x-*` keys that cause podlet to error.

If podlet handles your compose file without errors, you don't need any hacks.
