# TODO

## Completed

- [x] Split `utils/converters.py` into per-domain files under `utils/converters/`
  - `service.py` — port, volume, environment, healthcheck, cap_add/cap_drop, device, tmpfs, shm_size, log_driver, log_tag, sysctl, userns, hostnamemap, pull_policy, restart, label converters
  - `build.py` — build context, dockerfile, args, tags converters
  - `network.py` — network name and internal converters
  - `volume.py` — volume name converter
  - `_helpers.py` — shared utilities (key_val_to_quadlet, list_to_quadlet)
  - `_duration.py` — duration string parsing (Go-style → systemd)
  - `_list_or_dict.py` — list/dict normalization
- [x] Create `utils/field_maps/` with declarative mapping tables
  - `service.py` — `SERVICE_FIELD_MAP`
  - `build.py` — `BUILD_FIELD_MAP`
  - `network.py` — `NETWORK_FIELD_MAP`
  - `volume.py` — `VOLUME_FIELD_MAP`
- [x] Rewrite `utils/mapping.py` as thin orchestrator
  - Generic `_apply_field_map()` replaces per-type imperative code
  - `map_compose()` is the single entry point
  - `QuadletBundle` dataclass holds all generated units
  - **Bug fix:** Pod name mismatch — pod unit's `PodName` and container's `Pod` reference now both use `{project_name}-pod`
- [x] Remove all `compose_spec` and `podlet` imports/references
  - `utils/mapping.py` → `from models.compose import ...`
  - `utils/compose.py` → uses `ryaml.load()` + `ComposeSpecification.model_validate()`
- [x] Update project metadata
  - `pyproject.toml` — license Apache-2.0, deps: pydantic + ryaml + rich
  - `requirements.txt` — pydantic, ryaml[libyaml], rich
  - `flake.nix` — remove podlet dep, add ryaml, license = asl20
  - `AGENTS.md` — updated architecture diagram and field map docs
  - `README.md` — cleaned up, Apache 2.0 license
- [x] Fix `curl -o` command in `regenerate-models.yml` (was missing output filename)
- [x] Remove obsolete `test.py` scratch file
- [x] Extract `QuadletUnit` base class (`models/quadlet/_base.py`) to eliminate duplication
- [x] Add project labeling, service names, and `compose_path` to mapping layer
- [x] Create `commands/` package with CLI dispatch (`quadlet_compose.py`)
- [x] Replace PyYAML with ryaml in compose parser
- [x] Implement `compose_up` command (fully functional)
- [x] Add `commands/__init__.py` — registers all 13 commands
- [x] Add `utils/converters/__init__.py` — re-exports all converters
- [x] Add `utils/field_maps/__init__.py` — re-exports all field maps
- [x] Implement many service field converters previously listed as missing:
  - `convert_dns` / `convert_dns_search` → `DNS` / `DNSSearch`
  - `convert_extra_hosts` → `AddHost`
  - `convert_group_add` → `GroupAdd`
  - `convert_init` → `RunInit`
  - `convert_secrets` → `Secret`
  - `convert_stop_grace_period` → `StopTimeout` (duration converter)
  - `convert_stop_signal` → `StopSignal`
  - `convert_ulimits` → `Ulimit` (dict with soft/hard)
  - `convert_cgroup` → `CgroupsMode`
  - `convert_healthcheck` — handles `disable: true` → `HealthCmd=none`
  - `convert_volumes` — handles `tmpfs:` type
  - `convert_pull_policy` → `Pull`

## Remaining Work

### Command modules (`commands/`) — 12 stubs need implementation

Only `compose_up` is fully implemented. All others raise `NotImplementedError`:

- [ ] **`compose_down.py`** — `systemctl stop` → remove quadlet files → `podman pod rm`
- [ ] **`compose_convert.py`** — preview quadlet file output (dry-run of `up`)
- [ ] **`compose_config.py`** — validate and print compose config
- [ ] **`compose_build.py`** — trigger builds via systemd or podman
- [ ] **`compose_pull.py`** — pull images for all services
- [ ] **`compose_restart.py`** — `systemctl restart` for project services
- [ ] **`compose_ps.py`** — list running containers for project
- [ ] **`compose_logs.py`** — `journalctl` logs for project containers
- [ ] **`compose_images.py`** — list images used by project
- [ ] **`compose_port.py`** — print public port for a port binding
- [ ] **`compose_top.py`** — display running processes in containers
- [ ] **`compose_version.py`** — show version information

### Converters — edge cases & missing implementations

- [ ] **`convert_ports`** — verify IPv6 bracket notation handling (`[::1]:80:80`)
- [ ] **`convert_volumes`** — handle `nfs:` driver options
- [ ] **`convert_environment`** — verify `env_file` support (compose `env_file` → Quadlet has no direct equivalent)
- [ ] **`convert_deploy`** — compose `deploy.resources.limits` → Quadlet resource limits (not yet mapped)

### Field maps — missing compose fields

- [ ] `blkio_config` → no direct Quadlet equivalent (document as unsupported)
- [ ] `cpu_count` → no Quadlet equivalent (macOS only, skip)
- [ ] `cpu_percent` → no Quadlet equivalent (Windows only, skip)
- [ ] `configs` → Quadlet `Secret` or `Config` (needs investigation)
- [ ] `credential_spec` → no Quadlet equivalent (Windows only, skip)
- [ ] `domainname` → Quadlet `HostName=` (needs mapping)
- [ ] `ipc` → Quadlet `ShmemSize=` or `IPC=` (needs investigation)
- [ ] `mac_address` → Quadlet `MACAddress=` (needs mapping)
- [ ] `mem_swappiness` → no Quadlet equivalent (document as unsupported)
- [ ] `network_mode` → handle `service:` and `container:` prefixes
- [ ] `oom_kill_disable` → Quadlet `OOMScoreAdjust=` (needs investigation)
- [ ] `pid` → Quadlet `PID=` (needs mapping)
- [ ] `platform` → Quadlet `ImageArch=` / `ImageOS=` (needs investigation)
- [ ] `profiles` → no Quadlet equivalent (compose-only concept)
- [ ] `runtime` → no Quadlet equivalent (document as unsupported)
- [ ] `security_opt` → Quadlet `SecurityLabelDisable=` etc. (needs converter)
- [ ] `storage_opt` → no Quadlet equivalent (document as unsupported)
- [ ] `uts` → Quadlet `UTS=` (needs mapping)

### Testing

- [ ] Create `tests/unit/` directory structure
- [ ] Unit tests for all converter functions in `utils/converters/`
  - [ ] `test_service.py` — ports, volumes, environment, healthcheck, etc.
  - [ ] `test_build.py` — context, dockerfile, args, tags
  - [ ] `test_network.py` — name, internal
  - [ ] `test_volume.py` — name
  - [ ] `test_duration.py` — Go duration → systemd duration
  - [ ] `test_list_or_dict.py` — normalization edge cases
- [ ] Unit tests for field maps in `utils/field_maps/`
  - [ ] Verify every entry maps to a valid Quadlet field
- [ ] Unit tests for `utils/mapping.py`
  - [ ] Round-trip: compose dict → `QuadletBundle` → quadlet INI strings
  - [ ] Pod name consistency (PodName == container Pod reference)
  - [ ] Network name consistency
  - [ ] Volume name consistency
- [ ] Unit tests for `utils/compose.py`
  - [ ] `resolve_compose_path()` — file search order
  - [ ] `parse_compose()` — validation errors
- [ ] Integration tests (`tests/integration/`)
  - [ ] `test_up.py` — full compose → systemctl start cycle
  - [ ] `test_down.py` — systemctl stop → cleanup cycle
  - [ ] Requires: podman, systemd user session, lingering enabled

### Infrastructure

- [ ] Regenerate `models/compose.py` from latest `compose-spec.json` (run `datamodel-codegen`)
- [ ] Verify `flake.nix` builds: `nix build`
- [ ] Verify `nix flake check` passes
- [ ] Add CI workflow for unit tests (run on PR) — `tests.yml` exists but no `tests/` dir yet

### Documentation

- [ ] Create `docs/` directory with architecture and usage docs (syncs to GitHub Wiki via `sync-wiki.yml`)
- [ ] Add converter function docstrings (Google-style) — partially done
- [ ] Add field map docstrings explaining the tuple format — partially done
- [ ] Document unsupported compose fields and why
