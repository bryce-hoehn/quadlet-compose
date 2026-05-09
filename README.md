# podlet-compose

A thin wrapper around [podlet](https://github.com/containers/podlet) that acts as a drop-in replacement for `docker-compose` / `podman-compose`. It uses podlet to generate systemd quadlet service files from a `compose.yaml` and manages them via `systemctl`.

**Disclaimer** - This is currently only a **PROOF OF CONCEPT**. It has not been used in production and I do not recommend doing so.

## Quick Start

Install latest release from PyPi (recommended)

```bash
pip install podlet-compose
```

See [Installation](https://github.com/bryce-hoehn/podlet-compose/wiki/Installation) for more installation options.
## Usage

```
Usage: podlet-compose [OPTIONS] COMMAND

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

- [podlet](https://github.com/containers/podlet) — generates quadlet files from compose configs
- [podman](https://podman.io/) — container runtime
- Python 3.10+
- [rich](https://pypi.org/project/rich/)
- [ruamel.yaml](https://pypi.org/project/ruamel.yaml/)

## Hacks (Podlet Workarounds)

All compose file transformations are **enabled by default**. Disable them via `PODLET_COMPOSE_HACKS`:

```bash
# Disable all hacks
PODLET_COMPOSE_HACKS=false podlet-compose up
```

Available hacks: `interpolate`, `name_inject`, `normalize`, `expand`, `strip_extensions`. See the [Hacks](https://github.com/bryce-hoehn/podlet-compose/wiki/Hacks) wiki page for details.

## Documentation

Full documentation is available in the [GitHub Wiki](https://github.com/bryce-hoehn/podlet-compose/wiki):

- **[Installation](https://github.com/bryce-hoehn/podlet-compose/wiki/Installation)** — Pip, PyInstaller binary, Nix, and podman compose provider setup
- **[Commands](https://github.com/bryce-hoehn/podlet-compose/wiki/Commands)** — Full command reference
- **[How It Works](https://github.com/bryce-hoehn/podlet-compose/wiki/How-It-Works)** — Technical architecture and internals
- **[Hacks](https://github.com/bryce-hoehn/podlet-compose/wiki/Hacks)** — Podlet workarounds (enabled by default)
- **[Limitations](https://github.com/bryce-hoehn/podlet-compose/wiki/Limitations)** — Known limitations

## License

GNU General Public License v3.0


<a href="https://www.buymeacoffee.com/bhoehn" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>
