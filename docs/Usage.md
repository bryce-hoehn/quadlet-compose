# Usage

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
  down                 Stop and remove containers, networks, images, and volumes
  build                Build or rebuild services
  exec                 Execute a command in a running service container
  kill                 Kill containers
  pull                 Pull service images
  restart              Restart service containers
  run                  Run a one-off command in a new container
  ps                   List containers
  logs                 View output from containers
  top                  Display running processes
  images               List images
  port                 Print the public port for a port binding
  config               Validate and view compose config
  convert              Preview quadlet files
  version              Show version information
```
