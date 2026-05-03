import argparse
import sys

from rich.console import Console
from rich.text import Text

from compose_cmds import (
    compose_up,
    compose_down,
    compose_build,
    compose_pull,
    compose_restart,
    compose_ps,
    compose_logs,
    compose_stop,
    compose_start,
    compose_top,
    compose_images,
    compose_port,
    compose_version,
    compose_config,
    compose_convert,
)
from utils import ComposeError


def print_help() -> None:
    """Print styled help output in docker-compose format using rich."""
    console = Console()
    console.print(
        Text("Usage:", style="bold dark_orange"),
        "podlet-compose [OPTIONS] COMMAND",
    )
    console.print()
    console.print(
        "Generate systemd quadlet files from compose.yaml and manage services via systemctl."
    )
    console.print()
    console.print("Options:", style="bold dark_orange")
    console.print(
        "     ",
        Text("--dry-run", style="cyan"),
        "       Print commands without executing",
    )
    console.print(
        " ",
        Text("-f, --file", style="cyan"),
        "          Compose configuration files",
    )
    console.print(
        " ",
        Text("-h, --help", style="cyan"),
        "          Print help information",
    )
    console.print(
        " ",
        Text("-p, --project-name", style="cyan"),
        "  Specify an alternate project name",
    )
    console.print()
    console.print("Commands:", style="bold dark_orange")
    for cmd in COMMANDS:
        console.print(
            "  ", Text(f"{cmd['name']:<16}", style="cyan"), cmd["help"], sep=""
        )
    console.print()


COMMANDS = [
    {
        "name": "up",
        "help": "Create and start containers",
        "func": compose_up,
        "args": [("--kube", {"action": "store_true", "default": False})],
    },
    {
        "name": "down",
        "help": "Stop and remove containers",
        "func": compose_down,
        "args": [("--remove-files", {"action": "store_true"})],
    },
    {"name": "restart", "help": "Restart service containers", "func": compose_restart},
    {"name": "start", "help": "Start services", "func": compose_start},
    {"name": "stop", "help": "Stop services", "func": compose_stop},
    {
        "name": "build",
        "help": "Build or rebuild services",
        "func": compose_build,
        "args": [("service", {"nargs": "?", "default": None})],
    },
    {
        "name": "pull",
        "help": "Pull service images",
        "func": compose_pull,
        "args": [("service", {"nargs": "?", "default": None})],
    },
    {"name": "ps", "help": "List containers", "func": compose_ps},
    {
        "name": "logs",
        "help": "View output from containers",
        "func": compose_logs,
        "args": [("service", {"nargs": "?", "default": None})],
    },
    {"name": "top", "help": "Display running processes", "func": compose_top},
    {"name": "images", "help": "List images", "func": compose_images},
    {
        "name": "port",
        "help": "Print the public port for a port binding",
        "func": compose_port,
        "args": [("service", {"nargs": "?", "default": None})],
    },
    {
        "name": "config",
        "help": "Validate and view compose config",
        "func": compose_config,
    },
    {
        "name": "convert",
        "help": "Preview quadlet files",
        "func": compose_convert,
        "args": [("--kube", {"action": "store_true", "default": False})],
    },
    {"name": "version", "help": "Show version information", "func": compose_version},
]


def main() -> None:
    """Parse CLI arguments and dispatch to the appropriate compose command."""
    parser = argparse.ArgumentParser(
        prog="podlet-compose",
        add_help=False,
    )

    # Global options
    parser.add_argument("-f", "--file", dest="compose_file", default=None)
    parser.add_argument("-p", "--project-name", dest="project_name", default=None)
    parser.add_argument("--dry-run", action="store_true", dest="dry_run")
    parser.add_argument("-h", "--help", action="store_true", dest="show_help")

    subparsers = parser.add_subparsers(dest="command")
    for cmd in COMMANDS:
        p = subparsers.add_parser(cmd["name"])
        for arg_name, arg_kwargs in cmd.get("args", []):
            p.add_argument(arg_name, **arg_kwargs)
        p.set_defaults(func=cmd["func"])

    args = parser.parse_args()

    if args.show_help or not args.command:
        print_help()
        sys.exit(0)

    # Enable dry-run mode globally
    if args.dry_run:
        import utils.utils as _utils

        _utils.DRY_RUN = True

    try:
        args.func(
            compose_file=args.compose_file,
            remove_files=getattr(args, "remove_files", False),
            service=getattr(args, "service", None),
            kube=getattr(args, "kube", False),
        )
    except (ComposeError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
