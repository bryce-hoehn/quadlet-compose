# quadlet-compose

A Python-native compose→quadlet compiler that acts as a drop-in replacement for `docker-compose` / `podman-compose`. It parses `compose.yaml` files using [ryaml](https://pypi.org/project/ryaml/) and auto-generated [Pydantic](https://docs.pydantic.dev/) models from the [compose-spec](https://github.com/compose-spec/compose-spec) JSON Schema, translates them into Podman Quadlet unit files via a declarative mapping layer, and manages the resulting systemd services via `systemctl`.

**Disclaimer** - This is currently only a **PROOF OF CONCEPT**. It has not been used in production and I do not recommend doing so.

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
  down                 Stop and remove containers
  restart              Restart service containers
  start                Start services
  stop                 Stop services
  build                Build or rebuild services
  pull                 Pull service images
  ps                   List containers
  logs                 View output from containers
  top                  Display running processes
  images               List images
  port                 Print the public port for a port binding
  config               Validate and view compose config
  convert              Preview quadlet files
  version              Show version information
```

## Requirements

- [podman](https://podman.io/) — container runtime
- Python 3.10+
- [ryaml](https://pypi.org/project/ryaml/) — YAML parsing
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
