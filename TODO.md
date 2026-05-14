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
  - `utils/compose.py` → uses `yaml.safe_load()` + `ComposeSpecification.model_validate()`
- [x] Update project metadata
  - `pyproject.toml` — license Apache-2.0, deps: pydantic + pyyaml + rich
  - `requirements.txt` — pydantic, pyyaml[libyaml], rich
  - `flake.nix` — remove podlet dep, add pyyaml, license = asl20
  - `AGENTS.md` — updated architecture diagram and field map docs
  - `README.md` — cleaned up, Apache 2.0 license
- [x] Fix `curl -o` command in `regenerate-models.yml` (was missing output filename)
- [x] Remove obsolete `test.py` scratch file

## Remaining Work

### Converters — edge cases & missing implementations

- [ ] **`convert_ports`** — verify IPv6 bracket notation handling (`[::1]:80:80`)
- [ ] **`convert_volumes`** — handle `tmpfs:` type and `nfs:` driver options
- [ ] **`convert_healthcheck`** — handle `disable: true` mapping (currently maps to `HealthCmd=none`)
- [ ] **`convert_environment`** — verify `env_file` support (compose `env_file` → Quadlet has no direct equivalent)
- [ ] **`convert_deploy`** — compose `deploy.resources.limits` → Quadlet resource limits (not yet mapped)
- [ ] **`convert_cgroupns`** — compose `cgroup` field → Quadlet `CgroupsMode=` (not yet mapped)

### Field maps — missing compose fields

- [ ] `blkio_config` → no direct Quadlet equivalent (document as unsupported)
- [ ] `cpu_count` → no Quadlet equivalent (macOS only, skip)
- [ ] `cpu_percent` → no Quadlet equivalent (Windows only, skip)
- [ ] `configs` → Quadlet `Secret` or `Config` (needs investigation)
- [ ] `credential_spec` → no Quadlet equivalent (Windows only, skip)
- [ ] `dns` / `dns_search` → Quadlet `DNS=` (needs converter)
- [ ] `domainname` → Quadlet `HostName=` (needs mapping)
- [ ] `extra_hosts` → Quadlet `AddHost=` (needs converter)
- [ ] `group_add` → Quadlet `Group=` (needs converter)
- [ ] `init` → Quadlet `Init=` (simple boolean mapping)
- [ ] `ipc` → Quadlet `ShmemSize=` or `IPC=` (needs investigation)
- [ ] `mac_address` → Quadlet `MACAddress=` (needs mapping)
- [ ] `mem_swappiness` → no Quadlet equivalent (document as unsupported)
- [ ] `network_mode` → handle `service:` and `container:` prefixes
- [ ] `oom_kill_disable` → Quadlet `OOMScoreAdjust=` (needs investigation)
- [ ] `pid` → Quadlet `PID=` (needs mapping)
- [ ] `platform` → Quadlet `ImageArch=` / `ImageOS=` (needs investigation)
- [ ] `profiles` → no Quadlet equivalent (compose-only concept)
- [ ] `runtime` → no Quadlet equivalent (document as unsupported)
- [ ] `secrets` → Quadlet `Secret=` (needs converter)
- [ ] `security_opt` → Quadlet `SecurityLabelDisable=` etc. (needs converter)
- [ ] `stop_grace_period` → Quadlet `StopTimeout=` (needs duration converter)
- [ ] `storage_opt` → no Quadlet equivalent (document as unsupported)
- [ ] `ulimits` → Quadlet `LimitNPROC=` etc. (needs converter)
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

### Command modules (`compose_cmds/`)

- [ ] Verify all command modules work with new mapping layer
  - [ ] `up.py` — uses `map_compose()` → writes quadlet files → `systemctl start`
  - [ ] `down.py` — `systemctl stop` → removes quadlet files → `podman pod rm`
  - [ ] `build.py` — verify build context mapping
  - [ ] `config.py` — verify compose validation output
  - [ ] `convert.py` — verify quadlet file preview
  - [ ] `images.py`, `logs.py`, `port.py`, `ps.py`, `pull.py`, `restart.py`, `top.py`, `version.py`

### Infrastructure

- [ ] Regenerate `models/compose.py` from latest `compose-spec.json` (run `datamodel-codegen`)
- [ ] Verify `flake.nix` builds: `nix build`
- [ ] Verify `nix flake check` passes
- [ ] Add CI workflow for unit tests (run on PR)
- [ ] Add `compose_cmds/__init__.py` if missing — register all commands
- [ ] Add `utils/converters/__init__.py` — re-export all converters
- [ ] Add `utils/field_maps/__init__.py` — re-export all field maps

### Documentation

- [ ] Update `docs/` (if it exists) to reflect new architecture
- [ ] Add converter function docstrings (Google-style)
- [ ] Add field map docstrings explaining the tuple format
- [ ] Document unsupported compose fields and why
