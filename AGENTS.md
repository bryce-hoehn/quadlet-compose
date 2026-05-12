# quadlet-compose

A thin wrapper around [podlet](https://github.com/containers/podlet) that acts as a drop-in replacement for `docker-compose` / `podman-compose`. It translates `compose.yaml` files into Podman Quadlet units and manages them via `systemctl`.

## Architecture

```
quadlet_compose.py        # CLI entry point (argparse + rich)
├── compose_cmds/        # One module per docker-compose command
│   ├── up.py            #   podlet compose → quadlet files → systemctl start
│   ├── down.py          #   systemctl stop → rm quadlet files → podman pod rm
│   └── ...              #   build, config, convert, images, logs, port, ps, pull, restart, top, version
├── hacks/               # Optional compose.yaml transformations (disabled by default)
│   ├── interpolate.py   #   $VAR substitution
│   ├── name_inject.py   #   Inject project name into service names
│   ├── normalize.py     #   Normalize compose keys
│   ├── expand.py        #   Expand short-form syntax to long-form
│   └── strip_extensions.py  # Remove unsupported compose extensions
└── utils/
    ├── compose.py       #   Compose file parsing & validation
    ├── config.py        #   ~/.config/containers/systemd path helpers
    ├── progress.py      #   Rich-based progress display
    └── utils.py         #   run_cmd, ComposeError, DRY_RUN
```

## Design Principles

- **Delegate, don't reimplement.** Hand off all heavy lifting to `podlet` (quadlet generation) and `systemd`/`systemctl` (service lifecycle). quadlet-compose is a glue layer, not a runtime.
- **docker-compose parity only.** Do not implement features beyond what `docker-compose` provides. If docker-compose doesn't do it, quadlet-compose shouldn't either. New commands must map to an existing `docker-compose` subcommand.
- **Prefer Nix tooling.** Use `nix develop` for local development, `nix flake check` for validation, and Nix store paths for CI dependencies. Avoid installing packages via `apt` when a Nix equivalent exists.
- **Keep the surface area small.** Each `compose_cmds/*.py` module should be a thin translation layer: parse compose config → call podlet → call systemctl. Business logic lives in podlet and systemd, not here.

## Code Style

- Python 3.10+ (use `X | Y` union syntax, `match` is fine but not required)
- Single quotes for strings, double quotes inside f-strings when needed
- Use `from utils import run_cmd, ComposeError` for subprocess calls — never call `subprocess.run` directly in command modules
- Use `rich` for all terminal output; avoid bare `print()`
- Keep modules under ~300 lines; split if they grow beyond that

## Testing

- Unit tests: `nix develop -c pytest -v -m "not integration"`
- Integration tests: `nix develop -c pytest -v -m integration --timeout=120`
- Integration tests require: podman, podlet, systemd user session, lingering enabled
- All new compose commands must have at least a unit test for argument parsing
- All new hacks must have unit tests covering edge cases

## Common Patterns

### Running a subprocess

```python
from utils import run_cmd, ComposeError

# Raises ComposeError on failure
result = run_cmd(["podlet", "--unit-directory", str(unit_dir), "compose", "--pod", str(compose_path)], quiet=True)

# Capture output
stdout = result.stdout
```

### Adding a new compose command

1. Create `compose_cmds/<command>.py` with a `compose_<command>(compose_file, **kwargs)` function
2. Import and register it in `compose_cmds/__init__.py`
3. Add the CLI entry in `quadlet_compose.py`
4. Add unit tests in `tests/unit/`

### Adding a new hack

1. Create `hacks/<name>.py` with a function that transforms compose data
2. Register it in `hacks/__init__.py`
3. Add it to the `QUADLET_COMPOSE_HACKS` env var handling
4. Add tests in `tests/unit/`

## CI Notes

- GitHub Actions workflows use `actions/checkout@v6`
- The `release` job needs `prepare` in its `needs` list to access version outputs
- The Quadlet systemd generator must be symlinked from the Nix store to `~/.config/systemd/user-generators/` **after** `nix develop` has populated the store
- Use `nix path-info nixpkgs#podman` to resolve the generator path instead of searching `/nix/store`

## Maintenance

- **Update this file** when adding new commands, hacks, or changing architecture
- **Update `docs/`** when changing user-facing behavior — these sync to the GitHub Wiki via CI
- **Update `flake.nix`** version when bumping `pyproject.toml` version — they must stay in sync
- **Update `requirements.txt`** when adding or removing Python dependencies
