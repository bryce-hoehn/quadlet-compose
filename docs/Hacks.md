# Hacks (Podlet Workarounds)

podlet-compose includes workarounds for known podlet limitations and compose file transformations. **All hacks are enabled by default** — your compose file is automatically transformed before being passed to podlet.

Disable hacks via the `PODLET_COMPOSE_HACKS` environment variable:

```bash
# Disable all hacks
PODLET_COMPOSE_HACKS=false podlet-compose up

# All hacks enabled (default)
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

## When to Disable Hacks

- Disable hacks if you want podlet to see your compose file exactly as-written, with no transformations applied.
- If podlet handles your compose file without errors, you can leave hacks enabled without issue.
