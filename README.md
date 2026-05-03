# podlet-compose

A thin wrapper around [podlet](https://github.com/containers/podlet) that acts as a drop-in replacement for `docker-compose` / `podman-compose`. It uses podlet to generate systemd quadlet service files from a `compose.yaml` and manages them via `systemctl`.

**Disclaimer** - This is currently only a **PROOF OF CONCEPT**. It has not been used in production and I do not recommend doing so.

## Requirements

- [podlet](https://github.com/containers/podlet) — generates quadlet files from compose configs
- [podman](https://podman.io/) — container runtime
- Python 3.10+
- [PyYAML](https://pypi.org/project/PyYAML/)
- [rich](https://pypi.org/project/rich/)

## Installation

### Pip

Install the latest development version from GitHub:

```bash
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
sudo mv podlet-compose /usr/local/bin/
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
  up              Create and start containers
  down            Stop and remove containers
  restart         Restart service containers
  start           Start services
  stop            Stop services
  build           Build or rebuild services
  pull            Pull service images
  ps              List containers
  logs            View output from containers
  top             Display running processes
  images          List images
  port            Print the public port for a port binding
  config          Validate and view compose config
  convert         Preview quadlet files
  version         Show version information
```

### Global Options

#### `--dry-run`

Print commands that would be executed without actually running them. Useful for previewing what `up`, `down`, `restart`, etc. will do.

```bash
podlet-compose --dry-run up
```

#### `-f, --file`

Specify a path to a compose file. When omitted, podlet-compose searches the current directory for `compose.yaml`, `compose.yml`, `docker-compose.yaml`, etc. (same order as podlet).

```bash
podlet-compose -f /path/to/compose.yaml up
```

#### `-p, --project-name`

Specify an alternate project name. Defaults to the `name:` field in the compose file, or the directory name if not set.

```bash
podlet-compose -p myproject up
```

### Commands

#### `up`

Generates quadlet files from `compose.yaml` using podlet, reloads the systemd daemon, and starts all defined services.

By default, `up` uses pod mode (`--pod`) which groups all services in a shared pod with a common network namespace — matching docker-compose's default networking behavior. It also passes `--overwrite` and `--absolute-host-paths` to podlet automatically.

##### `--kube`

Use `--kube` to generate a `.kube` quadlet file and Kubernetes YAML instead of separate `.container` files. This groups all services in a Kubernetes-style pod.

```bash
podlet-compose up
podlet-compose up --kube
```

#### `down`

Stops all services defined in the compose file. With `--remove-files`, also removes the generated quadlet files.

```bash
podlet-compose down
podlet-compose down --remove-files
```

#### `restart`

Restarts all services defined in the compose file.

```bash
podlet-compose restart
```

#### `start`

Starts services without regenerating quadlet files. Use this when the quadlet files are already installed and you just need to start the services.

```bash
podlet-compose start
```

#### `stop`

Stops services without removing the quadlet files. The services can be started again with `start`.

```bash
podlet-compose stop
```

#### `build`

Builds images for services that define a `build:` context in the compose file. Optionally specify a single service.

```bash
podlet-compose build
podlet-compose build myservice
```

#### `pull`

Pulls images for all services (or a specific service) defined in the compose file.

```bash
podlet-compose pull
podlet-compose pull myservice
```

#### `ps`

Shows the status of all services via `systemctl --user status`.

```bash
podlet-compose ps
```

#### `logs`

Views logs from all services (or a specific service) via `journalctl`.

```bash
podlet-compose logs
podlet-compose logs myservice
```

#### `top`

Displays a live stream of container resource usage statistics via `podman stats`.

```bash
podlet-compose top
```

#### `images`

Lists the images used by each service, parsed from the compose file.

```bash
podlet-compose images
```

#### `port`

Prints port bindings defined in the compose file. Optionally specify a service to filter.

```bash
podlet-compose port
podlet-compose port myservice
```

#### `config`

Validates and displays the parsed compose configuration. Shows the project name, services, volumes, networks, and the full normalized YAML.

```bash
podlet-compose config
```

#### `convert`

Previews the quadlet files that would be generated by `up` without actually installing them. Uses the same defaults as `up` (`--pod`, `--overwrite`, `--absolute-host-paths`).

```bash
podlet-compose convert
podlet-compose convert --kube
```

#### `version`

Shows the podlet-compose version.

```bash
podlet-compose version
```

## How it works

1. **`up`** runs `podlet compose --unit-directory --pod --overwrite --absolute-host-paths` to generate `.container` and `.pod` quadlet files in `~/.config/containers/systemd/`, then calls `systemctl --user daemon-reload` and `systemctl --user start` for the pod service. With `--kube`, it generates a `.kube` file and Kubernetes YAML instead.
2. **`down`** calls `systemctl --user stop` for the pod/kube service. With `--remove-files`, it also cleans up the generated quadlet files.
3. **`start`/`stop`/`restart`** detect the deployment mode (pod, kube, or plain) from existing quadlet files and call the corresponding `systemctl --user` commands on the appropriate target.
4. **`ps`** calls `systemctl --user status` on the pod/kube service or individual services.
5. **`logs`** calls `journalctl --user` for each service.
6. **`build`** parses the compose file for `build:` contexts and runs `podman build`.
7. **`pull`** parses the compose file for `image:` references and runs `podman pull`.
8. **`images`** and **`port`** parse the compose file directly — no subprocess calls.
9. **`top`** calls `podman stats` on the `systemd-<service>` containers.
10. **`config`** parses and validates the compose file, printing the normalized configuration.
11. **`convert`** runs `podlet compose` without `--unit-directory` to preview the generated quadlet files.

## License

GNU General Public License v3.0
