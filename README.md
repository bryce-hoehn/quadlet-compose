# podlet-compose

A thin wrapper around [podlet](https://github.com/containers/podlet) that acts as a drop-in replacement for `docker-compose` / `podman-compose`. It uses podlet to generate systemd quadlet service files from a `compose.yaml` and manages them via `systemctl`.

**Disclaimer** - This is currently only a **PROOF OF CONCEPT**. It has not been used in production and I do not recommend doing so.

## Quick Start

```bash
# Install
pip3 install https://github.com/bryce-hoehn/podlet-compose/archive/main.tar.gz
```

### Standalone binary (PyInstaller)

Generate a standalone binary using Docker or Podman. This script downloads the repo, builds a static binary using [PyInstaller](https://pyinstaller.org/) via [the Dockerfile](https://github.com/bryce-hoehn/podlet-compose/blob/main/Dockerfile), and places it in the current directory:

```bash
sh -c "$(curl -sSL https://raw.githubusercontent.com/bryce-hoehn/podlet-compose/main/scripts/download_and_build_podlet-compose.sh)"
```

Then move it to your PATH:

```bash
chmod +x podlet-compose
mv podlet-compose $HOME/.local/bin
```

Or if you already have the repo cloned, build locally:

```bash
sh scripts/generate_binary_using_dockerfile.sh
```

### Installing as a podman compose provider

podlet-compose can be registered as a [compose provider](https://docs.podman.io/en/latest/markdown/podman-compose.1.html) for `podman compose`, so that `podman compose up` uses podlet-compose instead of docker-compose or podman-compose.

1. Install podlet-compose:

   ```bash
   pip install .
   ```

2. Edit `~/.config/containers/containers.conf` (create it if it doesn't exist) and add:

   ```toml
   [engine]
   compose_providers = ["podlet-compose"]
   compose_warning_logs = false
   ```

3. Verify it works:

   ```bash
   podman compose up
   ```

You can also set the provider via the `PODMAN_COMPOSE_PROVIDER` environment variable:

```bash
export PODMAN_COMPOSE_PROVIDER=podlet-compose
podman compose up
```

**Note:** podman passes its own options (e.g., `--env-file`, `--profile`) to the compose provider. podlet-compose handles the core compose commands (`up`, `down`, `start`, `stop`, `restart`, `ps`, `logs`, `build`, `pull`) but may not support all podman compose options. Unsupported options will be reported as errors.

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
- [PyYAML](https://pypi.org/project/PyYAML/)
- [rich](https://pypi.org/project/rich/)

## Documentation

Full documentation is available in the [GitHub Wiki](https://github.com/bryce-hoehn/podlet-compose/wiki):

- **[Installation](https://github.com/bryce-hoehn/podlet-compose/wiki/Installation)** — Pip, PyInstaller binary, Nix, and podman compose provider setup
- **[Commands](https://github.com/bryce-hoehn/podlet-compose/wiki/Commands)** — Full command reference
- **[How It Works](https://github.com/bryce-hoehn/podlet-compose/wiki/How-It-Works)** — Technical architecture and internals
- **[Limitations](https://github.com/bryce-hoehn/podlet-compose/wiki/Limitations)** — Known limitations

## License

GNU General Public License v3.0
