# Field Compatibility

## Service fields

How compose service fields map to Quadlet `.container` keys.

### ✅ Mapped (compose → quadlet)

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

## Build fields

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

## Network fields

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

## Volume fields

| Compose field | Quadlet key | Status |
|---------------|-------------|--------|
| `name` | `VolumeName` | ✅ |
| `driver` | `Driver` | ✅ |
| `labels` | `Label` | ✅ |
| `external` | — | ⚠️ Skipped (managed outside Quadlet) |
| `driver_opts` | — | ❌ No Quadlet equivalent |
