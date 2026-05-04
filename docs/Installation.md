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


## Nix

To use in a NixOS config, add the flake input and reference the package. Example:

```nix
{
  description = "Podlet-compose NixOS Configuration";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    podlet-compose.url = "github:bryce-hoehn/podlet-compose";
  };

  outputs = {
    self, 
    nixpkgs,
    podlet-compose,
    ...   
  }@inputs: {
    nixosConfigurations = {
      my_hosename = nixpkgs.lib.nixosSystem {
        system = "x86_64-linux";
        modules = [
          ./configuration.nix
          ({ pkgs, ... }: {
            environment.systemPackages = [ podlet-compose.packages.${pkgs.system}.default ];
          })
        ];
      };
    };
  };
}
```

### Podman

```nix
  virtualisation.podman = {
    enable = true;
    dockerCompat = true; # optional, aliases docker -> podman
    dockerSocket.enable = false; # optional, defaults to false
    defaultNetwork.settings.dns_enabled = true; # i forget
  };
```

### Compose Provider

Make podlet-compose the default podman compose provider.

```nix
  virtualisation.containers.containersConf.settings = {
    containers = {
      userns = "keep-id"; # probably optional?
    };
    engine = {
      compose_providers = ["podlet-compose"]; # set podlet-compose as podman compose provider
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
    shell = pkgs.fish; # unrelated but fish is great
    linger = true; # <---
    autoSubUidGidRange = true; # i forget what this does
  };
```
