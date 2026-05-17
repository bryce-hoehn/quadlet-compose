# Variable Interpolation

`quadlet-compose` supports variable interpolation in compose files using a `string.Template` subclass adapted from docker-compose v1, with `.env` file loading via `python-dotenv`.

**Priority order** (highest to lowest):
1. CLI `--env KEY=VALUE` flags
2. `.env` file (located alongside the compose file)
3. Shell environment variables (`os.environ`)

**Supported syntax:**
- `$VAR` / `${VAR}` — direct substitution
- `$$` — literal `$` escaping
- `${VAR:-default}` — default value if unset or empty
- `${VAR-default}` — default value if unset
- `${VAR:?error}` — error if unset or empty
- `${VAR?error}` — error if unset
- `${VAR:+replacement}` — replacement if set and non-empty
- `${VAR+replacement}` — replacement if set

Use `--no-interpolate` with `config` or `convert` to disable interpolation and see raw variable references.
