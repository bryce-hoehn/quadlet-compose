# quadlet-compose

A Python-native compose→quadlet compiler that acts as a drop-in replacement for `docker-compose` / `podman-compose`. It parses `compose.yaml` files using [PyYAML](https://pypi.org/project/PyYAML/) and auto-generated [Pydantic](https://docs.pydantic.dev/) models from the [compose-spec](https://github.com/compose-spec/compose-spec) JSON Schema, translates them into Podman Quadlet unit files via a declarative mapping layer, and manages the resulting systemd services via `systemctl`.

> **Status:** Early alpha. Core compose→quadlet translation is functional. Most common commands are implemented. Not recommended for production use.

## Quick Start

Install latest release from PyPi (recommended)

```bash
pip install quadlet-compose
```

See [Installation](https://github.com/bryce-hoehn/quadlet-compose/wiki/Installation) for more installation options.

## Usage

```
Usage: quadlet-compose [OPTIONS] COMMAND

Generate systemd quadlet files from compose.yaml and manage services via systemctl.

Options:
      --dry-run        Print commands without executing
  -f, --file           Compose configuration files
  -h, --help           Print help information
  -p, --project-name   Specify an alternate project name

Commands:
  up                   Create and start containers
  down                 Stop and remove containers, networks, images, and volumes
  build                Build or rebuild services
  exec                 Execute a command in a running service container
  kill                 Kill containers
  pull                 Pull service images
  restart              Restart service containers
  run                  Run a one-off command in a new container
  ps                   List containers
  logs                 View output from containers
  top                  Display running processes
  images               List images
  port                 Print the public port for a port binding
  config               Validate and view compose config
  convert              Preview quadlet files
  version              Show version information
```

## Command Compatibility

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

## Requirements

- [podman](https://podman.io/) — container runtime
- Python 3.10+
- [PyYAML](https://pypi.org/project/PyYAML/) — YAML parsing
- [pydantic](https://pypi.org/project/pydantic/) — compose-spec model validation
- [rich](https://pypi.org/project/rich/) — terminal output

## Documentation

Full documentation is available in the [GitHub Wiki](https://github.com/bryce-hoehn/quadlet-compose/wiki):

- **[Installation](https://github.com/bryce-hoehn/quadlet-compose/wiki/Installation)** — Pip, PyInstaller binary, Nix, and podman compose provider setup
- **[Commands](https://github.com/bryce-hoehn/quadlet-compose/wiki/Commands)** — Full command reference
- **[How It Works](https://github.com/bryce-hoehn/quadlet-compose/wiki/How-It-Works)** — Technical architecture and internals
- **[Limitations](https://github.com/bryce-hoehn/quadlet-compose/wiki/Limitations)** — Known limitations

## License

Apache License 2.0


<a href="https://www.buymeacoffee.com/bhoehn" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>
