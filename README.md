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

## Variable Interpolation

`quadlet-compose` supports variable interpolation in compose files using a `string.Template` subclass adapted from docker-compose v1, with `.env` file loading via `python-dotenv`.

**Priority order** (highest to lowest):
1. `.env` file (located alongside the compose file)
2. CLI `--env KEY=VALUE` flags
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

## Field Compatibility

### Service fields

How compose service fields map to Quadlet `.container` keys.

#### ✅ Mapped (compose → quadlet)

| Compose field | Quadlet key | Notes |
|---------------|-------------|-------|
| `image` | `Image` | |
| `container_name` | `ContainerName` | |
| `hostname` | `HostName` | |
| `working_dir` | `WorkingDir` | |
| `entrypoint` | `Entrypoint` | |
| `command` | `Exec` | |
| `environment` | `Environment` | List or dict → `KEY=VALUE` lines |
| `env_file` | `EnvironmentFile` | |
| `ports` | `PublishPort` (on pod) | Short/long syntax → `HOST:PORT[/PROTO]`; migrated to the pod unit since Podman requires ports on pods |
| `expose` | `ExposeHostPort` | |
| `labels` | `Label` | List or dict → `KEY=VALUE` lines |
| `annotations` | `Annotation` | |
| `user` | `User` | `user:group` → `User` + `Group` |
| `group_add` | `GroupAdd` | |
| `cap_add` | `AddCapability` | |
| `cap_drop` | `DropCapability` | |
| `devices` | `AddDevice` | |
| `dns` | `DNS` | |
| `dns_opt` | `DNSOption` | |
| `dns_search` | `DNSSearch` | |
| `extra_hosts` | `AddHost` | |
| `networks` | `Network` | |
| `healthcheck` | `HealthCmd`, `HealthInterval`, etc. | 1:N expansion into multiple health keys |
| `logging` | `LogDriver`, `LogOpt` | 1:N expansion |
| `mem_limit` | `Memory` | Byte string → bytes |
| `pids_limit` | `PidsLimit` | |
| `shm_size` | `ShmSize` | |
| `sysctls` | `Sysctl` | |
| `tmpfs` | `Tmpfs` | |
| `ulimits` | `Ulimit` | Dict → `TYPE=SOFT:HARD` |
| `secrets` | `Secret` | |
| `configs` | *(handled)* | Mapped similar to secrets |
| `pull_policy` | `Pull` | Compose values → Quadlet values |
| `init` | `RunInit` | |
| `read_only` | `ReadOnly` | |
| `stop_signal` | `StopSignal` | |
| `stop_grace_period` | `StopTimeout` | Duration string → seconds |
| `cgroup` | `CgroupsMode` | `private`/`host` → Quadlet values |
| `volumes` | `Volume`, `Tmpfs` | 1:N expansion; bind mounts, named volumes, tmpfs; relative paths resolved against compose file directory |

#### ⚠️ Handled differently

| Compose field | Notes |
|---------------|-------|
| `restart` | No direct Quadlet key. `restart: always` → `systemctl --user enable` on the container unit. `restart: on-failure` → systemd `Restart=on-failure`. Not currently mapped. |
| `privileged` | No direct Quadlet key. Can be achieved via `PodmanArgs=--privileged`. Not currently mapped. |
| `network_mode` | Partially handled via `networks`. Modes like `host` or `none` need `PodmanArgs`. Not currently mapped. |
| `platform` | No direct Quadlet key. Can be passed via `PodmanArgs=--platform`. Not currently mapped. |
| `security_opt` | No direct Quadlet key. Can be passed via `PodmanArgs=--security-opt`. Not currently mapped. |
| `mac_address` | No direct Quadlet key. Can be passed via `PodmanArgs=--mac-address`. Not currently mapped. |
| `stdin_open` / `tty` | No Quadlet equivalent (interactive flags, not applicable to systemd services). |
| `pid` | No direct Quadlet key. Can be passed via `PodmanArgs=--pid`. Not currently mapped. |
| `uts` | No direct Quadlet key. Can be passed via `PodmanArgs=--uts`. Not currently mapped. |
| `userns_mode` | Maps to Quadlet `UserNS` but not currently in the field map. |
| `ipc` | No direct Quadlet key. Can be passed via `PodmanArgs=--ipc`. Not currently mapped. |
| `runtime` | No direct Quadlet key. Can be passed via `PodmanArgs=--runtime`. Not currently mapped. |
| `mem_reservation` | No direct Quadlet key. Can be passed via `PodmanArgs=--memory-reservation`. Not currently mapped. |
| `mem_swappiness` | No direct Quadlet key. Can be passed via `PodmanArgs=--memory-swappiness`. Not currently mapped. |
| `memswap_limit` | No direct Quadlet key. Can be passed via `PodmanArgs=--memory-swap`. Not currently mapped. |
| `oom_kill_disable` | No direct Quadlet key. Can be passed via `PodmanArgs=--oom-kill-disable`. Not currently mapped. |
| `oom_score_adj` | No direct Quadlet key. Can be passed via `PodmanArgs=--oom-score-adj`. Not currently mapped. |
| `cpus` | No direct Quadlet key. Can be passed via `PodmanArgs=--cpus`. Not currently mapped. |
| `cpu_count` | No direct Quadlet key. Can be passed via `PodmanArgs=--cpu-count`. Not currently mapped. |
| `cpu_percent` | No direct Quadlet key. Can be passed via `PodmanArgs=--cpu-percent`. Not currently mapped. |
| `cpu_shares` | No direct Quadlet key. Can be passed via `PodmanArgs=--cpu-shares`. Not currently mapped. |
| `cpu_quota` | No direct Quadlet key. Can be passed via `PodmanArgs=--cpu-quota`. Not currently mapped. |
| `cpu_period` | No direct Quadlet key. Can be passed via `PodmanArgs=--cpu-period`. Not currently mapped. |
| `cpuset` | No direct Quadlet key. Can be passed via `PodmanArgs=--cpuset-cpus`. Not currently mapped. |
| `storage_opt` | No direct Quadlet key. Can be passed via `PodmanArgs=--storage-opt`. Not currently mapped. |
| `device_cgroup_rules` | No direct Quadlet key. Can be passed via `PodmanArgs=--device-cgroup-rule`. Not currently mapped. |
| `gpus` | No direct Quadlet key. Can be passed via `PodmanArgs=--gpus`. Not currently mapped. |

#### ❌ Not applicable / no Quadlet equivalent

| Compose field | Reason |
|---------------|--------|
| `build` | Handled separately via `.build` Quadlet units, not `.container` fields |
| `depends_on` | Service ordering is managed by systemd unit dependencies (auto-generated) |
| `extends` | Compose file preprocessing; resolved before mapping |
| `profiles` | Compose-level filtering; resolved before mapping |
| `scale` | No Quadlet equivalent; would require generating multiple container units |
| `links` | Legacy Docker feature; not supported by Podman |
| `external_links` | Legacy Docker feature; not supported by Podman |
| `domainname` | No Quadlet or podman equivalent |
| `isolation` | Windows/macOS-only; not applicable to Podman/Linux |
| `credential_spec` | Windows/DCV-specific; not applicable to Podman/Linux |
| `blkio_config` | No direct Quadlet key; limited podman support |
| `attach` | Not applicable to systemd-managed containers |
| `develop` | Docker Compose watch/dev feature; no Quadlet equivalent |
| `deploy` | Docker Swarm/EE feature; not applicable to Quadlet |
| `provider` | External provider delegation; not applicable to Quadlet |
| `models` | AI model feature; no Quadlet equivalent |
| `post_start` / `pre_stop` | Lifecycle hooks; no Quadlet equivalent |
| `label_file` | No Quadlet equivalent |
| `volumes_from` | No Quadlet equivalent |
| `use_api_socket` | Docker-specific; not applicable to Podman |
| `pull_refresh_after` | Compose-specific refresh policy; no Quadlet equivalent |
| `cpu_rt_period` / `cpu_rt_runtime` | No Quadlet key; limited podman support |

### Build fields

| Compose field | Quadlet key | Status |
|---------------|-------------|--------|
| `context` | `SetWorkingDirectory` | ✅ |
| `dockerfile` | `File` | ✅ |
| `target` | `Target` | ✅ |
| `pull` | `Pull` | ✅ |
| `network` | `Network` | ✅ |
| `args` | `Environment` | ✅ |
| `secrets` | `Secret` | ✅ |
| `labels` | `Label` | ✅ |
| `cache_from` | — | ❌ No Quadlet equivalent |
| `cache_to` | — | ❌ No Quadlet equivalent |
| `no_cache` | — | ❌ No Quadlet equivalent |
| `additional_contexts` | — | ❌ No Quadlet equivalent |
| `shm_size` | — | ❌ No Quadlet equivalent |
| `tags` | — | ❌ No Quadlet equivalent |
| `platforms` | — | ❌ No Quadlet equivalent |

### Network fields

| Compose field | Quadlet key | Status |
|---------------|-------------|--------|
| `name` | `NetworkName` | ✅ |
| `driver` | `Driver` | ✅ |
| `driver_opts` | `Options` | ✅ |
| `ipam` | `Subnet`, `Gateway`, `IPRange`, `Driver` | ✅ 1:N expansion |
| `internal` | `Internal` | ✅ |
| `enable_ipv6` | `IPv6` | ✅ |
| `labels` | `Label` | ✅ |
| `external` | — | ⚠️ Skipped (managed outside Quadlet) |
| `attachable` | — | ❌ Docker Swarm feature |
| `name` (external) | — | ⚠️ Skipped (managed outside Quadlet) |

### Volume fields

| Compose field | Quadlet key | Status |
|---------------|-------------|--------|
| `name` | `VolumeName` | ✅ |
| `driver` | `Driver` | ✅ |
| `labels` | `Label` | ✅ |
| `external` | — | ⚠️ Skipped (managed outside Quadlet) |
| `driver_opts` | — | ❌ No Quadlet equivalent |

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
