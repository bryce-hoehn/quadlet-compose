# Command Compatibility

Comparison of `docker compose` commands against `quadlet-compose` support:

| docker compose | Status | Notes |
|----------------|--------|-------|
| `attach` | ❌ | |
| `build` | ✅ | Builds images via `podman build` from service build contexts |
| `commit` | ❌ | |
| `config` | ✅ | Validates and prints the compose configuration |
| `convert` | ✅ | Previews generated quadlet files without writing to disk |
| `cp` | ❌ | |
| `create` | ❌ | |
| `down` | ✅ | Stops systemd units, removes quadlet files, removes pod; supports `--rmi`, `--volumes` |
| `events` | ❌ | |
| `exec` | ✅ | Executes a command in a running container via `podman exec` |
| `export` | ❌ | |
| `images` | ✅ | Lists images via `podman images` filtered by project label |
| `kill` | ✅ | Kills containers via `systemctl --user kill`; supports `--signal` |
| `logs` | ✅ | Delegates to `podman logs`; supports `--follow`, `--since`, `--tail`, `--timestamps`, `--until` |
| `ls` | ❌ | |
| `pause` | ❌ | |
| `port` | ✅ | Prints public port for a port binding via `podman port` |
| `ps` | ✅ | Delegates to `podman ps`; supports `--all`, `--filter`, `--format`, `--services`, `--quiet`, `--status` |
| `publish` | ❌ | |
| `pull` | ✅ | Pulls service images via `podman pull`; supports `--quiet`, `--ignore-buildable`, `--ignore-pull-failures` |
| `push` | ❌ | |
| `restart` | ✅ | Delegates to `down` + `up` |
| `rm` | ❌ | |
| `run` | ✅ | Runs one-off commands via `podman run`; supports `-d`, `--entrypoint`, `-e`, `--name`, `-p`, `--rm`, `-u`, `-v`, `-w` |
| `scale` | ❌ | |
| `start` | ❌ | |
| `stats` | ❌ | |
| `stop` | ❌ | |
| `top` | ✅ | Displays running processes via `podman top`; accepts optional service list |
| `unpause` | ❌ | |
| `up` | ✅ | Parses compose, generates quadlet files, starts systemd units |
| `version` | ✅ | Supports `--format pretty\|json` and `--short` |
| `volumes` | ❌ | |
| `wait` | ❌ | |
| `watch` | ❌ | |
