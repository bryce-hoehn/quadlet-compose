# quadlet-compose

A Python-native compose→quadlet compiler that acts as a drop-in replacement for `docker-compose` / `podman-compose`. It parses `compose.yaml` files using [PyYAML](https://pypi.org/project/PyYAML/) and auto-generated [Pydantic](https://docs.pydantic.dev/) models from the [compose-spec](https://github.com/compose-spec/compose-spec) JSON Schema, translates them into Podman Quadlet unit files via a declarative mapping layer, and manages the resulting systemd services via `systemctl`.

> **Status:** Early alpha. Core compose→quadlet translation is functional. Most common commands are implemented. Not recommended for production use.

## Quick Start

Install latest release from PyPi (recommended)

```bash
pip install quadlet-compose
```

See [Installation](https://github.com/bryce-hoehn/quadlet-compose/wiki/Installation) for more installation options.

## Requirements

- [podman](https://podman.io/) — container runtime
- Python 3.10+
- [PyYAML](https://pypi.org/project/PyYAML/) — YAML parsing
- [pydantic](https://pypi.org/project/pydantic/) — compose-spec model validation
- [rich](https://pypi.org/project/rich/) — terminal output

## Documentation

- **[Installation](docs/Installation.md)** — Pip, PyInstaller binary, Nix, and podman compose provider setup
- **[Usage](docs/Usage.md)** — CLI commands and options
- **[Command Compatibility](docs/Command-Compatibility.md)** — `docker compose` command support matrix
- **[Variable Interpolation](docs/Variable-Interpolation.md)** — `.env` file loading and `$VAR` substitution syntax
- **[Field Compatibility](docs/Field-Compatibility.md)** — Compose→Quadlet field mapping tables (services, builds, networks, volumes)

## License

Apache License 2.0


<a href="https://www.buymeacoffee.com/bhoehn" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>
