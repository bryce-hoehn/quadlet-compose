# Installation

## Pip

Install the latest development version from GitHub:

```bash
pip3 install https://github.com/bryce-hoehn/podlet-compose/archive/main.tar.gz
```

## Standalone Binary (PyInstaller)

Generate a standalone binary using Docker or Podman. This script downloads the repo, builds a static binary using [PyInstaller](https://pyinstaller.org/) via [the Dockerfile](https://github.com/bryce-hoehn/podlet-compose/blob/main/Dockerfile), and places it in the current directory:

```bash
sh -c "$(curl -sSL https://raw.githubusercontent.com/bryce-hoehn/podlet-compose/main/scripts/download_and_build_podlet-compose.sh)"
```

Then move it to your PATH:

```bash
chmod +x podlet-compose
sudo mv podlet-compose ~/.local/bin/
```

## Nix

To use in a NixOS or home-manager config, add the flake input and reference the package:

```nix
inputs.podlet-compose.url = "github:bryce-hoehn/podlet-compose";

# In your system/home config:
environment.systemPackages = [ inputs.podlet-compose.packages.${system}.default ];
```

## Installing as a podman compose provider

podlet-compose can be registered as a [compose provider](https://docs.podman.io/en/latest/markdown/podman-compose.1.html) for `podman compose`, so that `podman compose up` uses podlet-compose instead of docker-compose or podman-compose.

Edit `~/.config/containers/containers.conf` (create it if it doesn't exist) and add:

   ```toml
   [engine]
   compose_providers = ["podlet-compose"]
   compose_warning_logs = false
   ```

You can also set the provider via the `PODMAN_COMPOSE_PROVIDER` environment variable:

```bash
export PODMAN_COMPOSE_PROVIDER=podlet-compose
podman compose up
```
