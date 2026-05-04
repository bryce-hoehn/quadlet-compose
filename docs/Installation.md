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
sudo mv podlet-compose /usr/local/bin/
```

Or if you already have the repo cloned, build locally:

```bash
sh scripts/generate_binary_using_dockerfile.sh
```

## Nix

Build and install using the flake:

```bash
# Install directly
nix profile install github:bryce-hoehn/podlet-binding

# Or run ad-hoc
nix run github:bryce-hoehn/podlet-binding -- up
```

To use a specific branch (e.g., `dev`):

```bash
nix profile install github:bryce-hoehn/podlet-binding/dev
```

If you have the repo cloned locally:

```bash
# Enter a dev shell with all dependencies
nix develop

# Build the package
nix build
./result/bin/podlet-compose --help
```

To use in a NixOS or home-manager config, add the flake input and reference the package:

```nix
inputs.podlet-compose.url = "github:bryce-hoehn/podlet-binding";

# In your system/home config:
environment.systemPackages = [ inputs.podlet-compose.packages.${system}.default ];
```

## Installing as a podman compose provider

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
