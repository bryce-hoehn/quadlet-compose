# quadlet-compose

A Python-native compose→quadlet compiler that acts as a drop-in replacement for `docker-compose` / `podman-compose`. It parses `compose.yaml` files using [PyYAML](https://pypi.org/project/PyYAML/) and auto-generated [Pydantic](https://docs.pydantic.dev/) models from the [compose-spec](https://github.com/compose-spec/compose-spec) JSON Schema, translates them into Podman Quadlet unit files via a declarative mapping layer, and manages the resulting systemd services via `systemctl`.

## Architecture

```
quadlet_compose.py        # CLI entry point (argparse + rich)
├── commands/         # One module per docker-compose command
│   ├── compose_up.py     #   map_compose() → write quadlet files → systemctl start
│   ├── compose_down.py   #   systemctl stop → rm quadlet files → podman pod rm
│   └── ...               #   build, config, convert, exec, images, kill, logs, port, ps, pull, restart, run, top, version
├── models/
│   ├── compose.py        #   Auto-generated Pydantic models from compose-spec.json (via datamodel-codegen)
│   └── quadlet/          #   Pydantic models for Quadlet INI unit types
│       ├── container.py  #     ContainerUnit → .container INI
│       ├── network.py    #     NetworkUnit → .network INI
│       ├── volume.py     #     VolumeUnit → .volume INI
│       ├── pod.py        #     PodUnit → .pod INI
│       ├── build.py      #     BuildUnit → .build INI
│       └── image.py      #     ImageUnit → .image INI
├── utils/
│   ├── compose.py        #   Compose file parsing (PyYAML + Pydantic validation)
│   ├── mapping.py        #   Compose→Quadlet mapping orchestrator (QuadletBundle)
│   ├── quadlet.py        #   ~/.config/containers/systemd path helpers
│   ├── converters/       #   Converter functions for compose→quadlet type transformations
│   │   ├── service.py    #     Service field converters (ports, volumes, healthcheck, etc.)
│   │   ├── build.py      #     Build field converters
│   │   ├── network.py    #     Network field converters
│   │   ├── volume.py     #     Volume field converters
│   │   ├── _helpers.py   #     Shared converter utilities
│   │   ├── _duration.py  #     Duration string parsing
│   │   └── _list_or_dict.py  # List/dict normalization converters
│   └── field_maps/       #   Declarative field mapping tables
│       ├── service.py    #     SERVICE_FIELD_MAP
│       ├── build.py      #     BUILD_FIELD_MAP
│       ├── network.py    #     NETWORK_FIELD_MAP
│       └── volume.py     #     VOLUME_FIELD_MAP
└── compose-spec.json     #   Official compose-spec JSON Schema (upstream)
```

### Data pipeline

```
compose.yaml
    ↓ yaml.safe_load()
compose data dict
    ↓ ComposeSpecification.model_validate() (Pydantic)
validated compose models
    ↓ map_compose() in utils/mapping.py
QuadletBundle { pod, containers, networks, volumes, builds }
    ↓ .to_quadlet_files()
{ "myapp.pod": "[Pod]\n...", "myapp-web.container": "[Container]\nImage=nginx:latest\n..." }
    ↓ write to ~/.config/containers/systemd/
systemctl --user daemon-reload && systemctl --user start <units>
```

### Mapping behaviors

The compose→quadlet mapping layer applies several transformations beyond
simple field renaming:

- **Pod references**: `Pod=` in `.container` files uses the full Quadlet
  filename (e.g., `Pod=myapp.pod`) so the Quadlet generator can resolve
  the reference.
- **Port migration**: `PublishPort` is moved from container units to the
  pod unit, since Podman requires ports on the pod when containers share
  its network namespace.
- **Relative path resolution**: Volume source paths starting with `./` or
  `../` are resolved against the compose file's parent directory before
  writing quadlet files (Quadlet would otherwise resolve them against
  `~/.config/containers/systemd/`).
- **Label handling**: Compose `labels` (list or dict) are converted to
  `Label=` lines. The auto-generated Pydantic models represent list-form
  labels as `set[str]`, which converters handle alongside `list[str]` and
  `dict`.

## Design Principles

- **Own the translation, delegate the parsing and lifecycle.** Use PyYAML for YAML parsing and Pydantic models (auto-generated from compose-spec JSON Schema) for validation. Use `systemctl` for service management. The compose→quadlet mapping is the core value of this project — it should be correct, complete, and well-tested.
- **Declarative mapping over imperative code.** Field maps (`SERVICE_FIELD_MAP`, `NETWORK_FIELD_MAP`, etc.) declare the compose→quadlet translation as data. Converter functions handle type transformations. This makes the mapping auditable, testable, and easy to extend.
- **docker-compose parity only.** Do not implement features beyond what `docker-compose` provides. If docker-compose doesn't do it, quadlet-compose shouldn't either. New commands must map to an existing `docker-compose` subcommand.
- **Prefer Nix tooling.** Use `nix develop` for local development, `nix flake check` for validation, and Nix store paths for CI dependencies. Avoid installing packages via `apt` when a Nix equivalent exists.
- **Keep the surface area small.** Each `commands/*.py` module should follow the pattern: parse compose → map to quadlet → write files → call systemctl. Business logic lives in the mapping layer and systemd, not in command modules.

## Code Style

- Python 3.10+ (use `X | Y` union syntax, `match` is fine but not required)
- Single quotes for strings, double quotes inside f-strings when needed
- Use `from utils import ComposeError` for error handling — never call `subprocess.run` directly in command modules
- Use `rich` for all terminal output; avoid bare `print()`
- Keep modules under ~300 lines; split if they grow beyond that

## Testing

- Unit tests: `nix develop -c pytest -v -m "not integration"`
- Integration tests: `nix develop -c pytest -v -m integration --timeout=120`
- Integration tests require: podman, systemd user session, lingering enabled
- All new compose commands must have at least a unit test for argument parsing
- All new converter functions must have unit tests covering edge cases
- Mapping layer tests should verify round-trip: compose dict → `QuadletBundle` → quadlet INI strings

## Common Patterns

### Mapping a compose service to a Quadlet container

```python
from utils.mapping import map_compose

# Parse compose file and map to quadlet units
bundle = map_compose(compose_data, project_name='myapp')

# Get all quadlet file contents
files = bundle.to_quadlet_files()
# {"myapp-pod.pod": "[Pod]\n...", "web.container": "[Container]\nImage=nginx:latest\n..."}

# Write to unit directory
from utils import get_unit_directory
unit_dir = get_unit_directory()
for filename, content in files.items():
    (unit_dir / filename).write_text(content)
```

### Adding a new field mapping

1. If it's a 1:1 rename (same type), add an entry to the relevant field map in `utils/field_maps/`:
   ```python
   ('compose_field', 'QuadletField', None),
   ```
2. If it needs type conversion, write a converter function in `utils/converters/` and reference it:
   ```python
   ('compose_field', 'QuadletField', convert_my_field),
   ```
3. Add unit tests in `tests/unit/test_mapping.py`

### Adding a new compose command

1. Create `commands/<command>.py` with a `compose_<command>(compose_file, **kwargs)` function
2. Import and register it in `commands/__init__.py`
3. Add the CLI entry in `quadlet_compose.py`
4. Add unit tests in `tests/unit/`

### Regenerating compose-spec models

The compose-spec Pydantic models in `models/compose.py` are auto-generated from `compose-spec.json`:

```bash
# Download latest schema
curl -o compose-spec.json https://raw.githubusercontent.com/compose-spec/compose-go/refs/heads/main/schema/compose-spec.json

# Regenerate models (reads [tool.datamodel-codegen] from pyproject.toml)
datamodel-codegen
```

This is automated via the `regenerate-models.yml` GitHub Actions workflow.

## CI Notes

- GitHub Actions workflows use `actions/checkout@v6`
- The `release` job needs `prepare` in its `needs` list to access version outputs
- The Quadlet systemd generator must be symlinked from the Nix store to `~/.config/systemd/user-generators/` **after** `nix develop` has populated the store
- Use `nix path-info nixpkgs#podman` to resolve the generator path instead of searching `/nix/store`

## Maintenance

- **Update this file** when adding new commands, field mappings, or changing architecture
- **Update `docs/`** when changing user-facing behavior — these sync to the GitHub Wiki via CI
- **Update `flake.nix`** version when bumping `pyproject.toml` version — they must stay in sync
- **Update `requirements.txt`** when adding or removing Python dependencies
