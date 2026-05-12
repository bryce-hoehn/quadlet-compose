# Installation

### Install the latest release version from PyPi (recommended):

```bash
pip install quadlet-compose
```

### Install the latest development version from GitHub:

```bash
pip3 install https://github.com/bryce-hoehn/quadlet-compose/archive/main.tar.gz
```

### Standalone Binary (PyInstaller)

Generate a standalone binary using Docker or Podman. This script downloads the repo, builds a static binary using [PyInstaller](https://pyinstaller.org/) via [the Dockerfile](https://github.com/bryce-hoehn/quadlet-compose/blob/main/Dockerfile), and places it in the current directory:

```bash
sh -c "$(curl -sSL https://raw.githubusercontent.com/bryce-hoehn/quadlet-compose/main/scripts/download_and_build_quadlet-compose.sh)"
```

Then move it to your PATH:

```bash
chmod +x quadlet-compose
sudo mv quadlet-compose ~/.local/bin/
```

# Installing as a podman compose provider

quadlet-compose can be registered as a [compose provider](https://docs.podman.io/en/latest/markdown/podman-compose.1.html) for `podman compose`, so that `podman compose up` uses quadlet-compose instead of docker-compose or podman-compose.

Edit `~/.config/containers/containers.conf` (create it if it doesn't exist) and add:

   ```toml
   [engine]
   compose_providers = ["quadlet-compose"]
   compose_warning_logs = false
   ```

You can also set the provider via the `PODMAN_COMPOSE_PROVIDER` environment variable:

```bash
export PODMAN_COMPOSE_PROVIDER=quadlet-compose
podman compose up
```


# Nix

### Flake

To use in a NixOS config, add the flake input and reference the package. Example:

```nix
{
  description = "quadlet-compose NixOS Configuration";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    quadlet-compose.url = "github:bryce-hoehn/quadlet-compose";
  };

  outputs = {
    self, 
    nixpkgs,
    quadlet-compose,
    ...   
  }@inputs: {
    nixosConfigurations = {
      my_hosename = nixpkgs.lib.nixosSystem {
        system = "x86_64-linux";
        modules = [
          ./configuration.nix
          ({ pkgs, ... }: {
            environment.systemPackages = [ quadlet-compose.packages.${pkgs.system}.default ];
          })
        ];
      };
    };
  };
}
```

### Podman

```nix
  virtualisation.containers.enable = true;
  virtualisation = {
    podman = {
      enable = true;

      # Create a `docker` alias for podman, to use it as a drop-in replacement
      dockerCompat = true;

      # Required for containers under podman-compose to be able to talk to each other.
      defaultNetwork.settings.dns_enabled = true;
    };
  };
```

### Compose Provider

Make quadlet-compose the default podman compose provider.

```nix
  virtualisation.containers.containersConf.settings = {
    containers = {
      userns = "keep-id"; # recommended. if you don't know what this does, keep it.
    };
    engine = {
      compose_providers = ["quadlet-compose"]; # set quadlet-compose as podman compose provider
      compose_warning_logs = false; # disables annoying podman compose warning
    };
  };
```

### Linger

Required for autostarting services.

```nix
  users.users.bryce = {
    isNormalUser = true;
    extraGroups = [ "wheel" "podman" ];
    linger = true; # <---
  };
```
