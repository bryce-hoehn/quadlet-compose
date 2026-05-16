import argparse
import sys

from rich.console import Console
from rich.text import Text

from utils import ComposeError
from subcommands import (
    build,
    config,
    convert,
    down,
    exec as exec_mod,
    images,
    kill,
    logs,
    port,
    ps,
    pull,
    restart,
    run,
    start,
    stop,
    top,
    up,
    version,
)

COMMANDS = [
    {"name": "up", "help": up.HELP, "func": up.compose_up, "args": up.ARGS},
    {"name": "down", "help": down.HELP, "func": down.compose_down, "args": down.ARGS},
    {
        "name": "exec",
        "help": exec_mod.HELP,
        "func": exec_mod.compose_exec,
        "args": exec_mod.ARGS,
    },
    {"name": "kill", "help": kill.HELP, "func": kill.compose_kill, "args": kill.ARGS},
    {"name": "run", "help": run.HELP, "func": run.compose_run, "args": run.ARGS},
    {
        "name": "restart",
        "help": restart.HELP,
        "func": restart.compose_restart,
        "args": restart.ARGS,
    },
    {
        "name": "start",
        "help": start.HELP,
        "func": start.compose_start,
        "args": start.ARGS,
    },
    {"name": "stop", "help": stop.HELP, "func": stop.compose_stop, "args": stop.ARGS},
    {
        "name": "build",
        "help": build.HELP,
        "func": build.compose_build,
        "args": build.ARGS,
    },
    {"name": "pull", "help": pull.HELP, "func": pull.compose_pull, "args": pull.ARGS},
    {"name": "ps", "help": ps.HELP, "func": ps.compose_ps, "args": ps.ARGS},
    {"name": "logs", "help": logs.HELP, "func": logs.compose_logs, "args": logs.ARGS},
    {"name": "top", "help": top.HELP, "func": top.compose_top, "args": top.ARGS},
    {
        "name": "images",
        "help": images.HELP,
        "func": images.compose_images,
        "args": images.ARGS,
    },
    {"name": "port", "help": port.HELP, "func": port.compose_port, "args": port.ARGS},
    {
        "name": "config",
        "help": config.HELP,
        "func": config.compose_config,
        "args": config.ARGS,
    },
    {
        "name": "convert",
        "help": convert.HELP,
        "func": convert.compose_convert,
        "args": convert.ARGS,
    },
    {
        "name": "version",
        "help": version.HELP,
        "func": version.compose_version,
        "args": version.ARGS,
    },
]


def print_help() -> None:
    """Print styled help output in docker-compose format using rich."""
    console = Console()
    console.print(
        Text("Usage:", style="bold dark_orange"),
        "quadlet-compose [OPTIONS] COMMAND",
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
        console.print(" ", Text(f"{cmd['name']:<16}", style="cyan"), "   ", cmd["help"])
    console.print()


def main() -> None:
    """Parse CLI arguments and dispatch to the appropriate compose command."""
    parser = argparse.ArgumentParser(
        prog="quadlet-compose",
        add_help=False,
    )

    # Global options
    parser.add_argument("-f", "--file", dest="compose_file", default=None)
    parser.add_argument("-p", "--project-name", dest="project_name", default=None)
    parser.add_argument("-h", "--help", action="store_true", dest="show_help")

    subparsers = parser.add_subparsers(dest="command")
    for cmd in COMMANDS:
        p = subparsers.add_parser(cmd["name"])
        for arg_names, arg_kwargs in cmd.get("args", []):
            if isinstance(arg_names, str):
                p.add_argument(arg_names, **arg_kwargs)
            else:
                p.add_argument(*arg_names, **arg_kwargs)
        p.set_defaults(func=cmd["func"])

    args = parser.parse_args()

    if args.show_help or not args.command:
        print_help()
        sys.exit(0)

    try:
        # Build kwargs from argparse namespace, skipping private/internal attrs
        skip = {"command", "func", "show_help", "compose_file", "project_name"}
        kwargs = {k: v for k, v in vars(args).items() if k not in skip}
        args.func(compose_file=args.compose_file, **kwargs)
    except (ValueError, ComposeError) as e:
        console = Console(stderr=True)
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
