# podlet-compose

A thin wrapper around [podlet](https://github.com/containers/podlet) that acts as a drop-in replacement for `docker-compose` / `podman-compose`. It uses podlet to generate systemd quadlet service files from a `compose.yaml` and manages them via `systemctl`.

**Disclaimer** - This is currently only a **PROOF OF CONCEPT**. It has not been used in production and I do not recommend doing so.

## Quick Start

```bash
# Install
pip3 install https://github.com/bryce-hoehn/podlet-compose/archive/main.tar.gz

# Use
cd /path/to/compose/project
podlet-compose up
```

## Requirements

- [podlet](https://github.com/containers/podlet) — generates quadlet files from compose configs
- [podman](https://podman.io/) — container runtime
- Python 3.10+
- [PyYAML](https://pypi.org/project/PyYAML/)
- [rich](https://pypi.org/project/rich/)

## Wiki Pages

- **[Installation](Installation)** — Pip, PyInstaller binary, Nix, and podman compose provider setup
- **[Commands](Commands)** — Full command reference
- **[How It Works](How-It-Works)** — Technical architecture and internals
- **[Limitations](Limitations)** — Known limitations (podlet-compose and inherited from podlet)

## License

GNU General Public License v3.0
