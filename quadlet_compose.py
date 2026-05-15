import argparse
import sys

from rich.console import Console
from rich.text import Text

from commands import (
    compose_up,
    compose_down,
    compose_build,
    compose_exec,
    compose_kill,
    compose_pull,
    compose_restart,
    compose_run,
    compose_start,
    compose_stop,
    compose_ps,
    compose_logs,
    compose_top,
    compose_images,
    compose_port,
    compose_version,
    compose_config,
    compose_convert,
)

COMMANDS = [
    {
        "name": "up",
        "help": "Create and start containers",
        "func": compose_up,
        "args": [
            (
                ("-d", "--detach"),
                {
                    "action": "store_true",
                    "default": False,
                    "help": "Run in background without following logs",
                },
            ),
            (
                "--remove-orphans",
                {
                    "action": "store_true",
                    "default": False,
                    "help": "Remove containers for services not defined in the Compose file",
                },
            ),
            (
                "--build",
                {
                    "action": "store_true",
                    "default": False,
                    "help": "Build images before starting containers",
                },
            ),
            (
                "--no-build",
                {
                    "action": "store_true",
                    "default": False,
                    "help": "Don't build an image, even if policy",
                },
            ),
            (
                "--quiet-build",
                {
                    "action": "store_true",
                    "default": False,
                    "help": "Suppress build output",
                },
            ),
            (
                "--pull",
                {
                    "choices": ["always", "missing", "never"],
                    "default": None,
                    "help": "Pull image before running",
                },
            ),
            (
                "--quiet-pull",
                {
                    "action": "store_true",
                    "default": False,
                    "help": "Pull without printing progress",
                },
            ),
            (
                "--force-recreate",
                {
                    "action": "store_true",
                    "default": False,
                    "help": "Recreate even if config unchanged",
                },
            ),
            (
                "--no-recreate",
                {
                    "action": "store_true",
                    "default": False,
                    "help": "Don't recreate existing containers",
                },
            ),
            (
                "--always-recreate-deps",
                {
                    "action": "store_true",
                    "default": False,
                    "help": "Recreate dependent containers",
                },
            ),
            (
                "--attach",
                {
                    "nargs": "*",
                    "default": None,
                    "help": "Restrict attaching to specified services",
                },
            ),
            (
                "--attach-dependencies",
                {
                    "action": "store_true",
                    "default": False,
                    "help": "Attach to log output of dependent services",
                },
            ),
            (
                "--no-attach",
                {
                    "nargs": "*",
                    "default": None,
                    "help": "Don't attach to specified services",
                },
            ),
            (
                "--no-color",
                {
                    "action": "store_true",
                    "default": False,
                    "help": "Produce monochrome output",
                },
            ),
            (
                "--no-log-prefix",
                {
                    "action": "store_true",
                    "default": False,
                    "help": "Don't print prefix in logs",
                },
            ),
            (
                "--timestamps",
                {"action": "store_true", "default": False, "help": "Show timestamps"},
            ),
            (
                "--abort-on-container-exit",
                {
                    "action": "store_true",
                    "default": False,
                    "help": "Stop all if any container stops",
                },
            ),
            (
                "--abort-on-container-failure",
                {
                    "action": "store_true",
                    "default": False,
                    "help": "Stop all if any container fails",
                },
            ),
            (
                "--exit-code-from",
                {"default": None, "help": "Return exit code of selected service"},
            ),
            (
                "--scale",
                {
                    "nargs": "*",
                    "default": None,
                    "help": "Scale SERVICE to NUM instances",
                },
            ),
            (
                ("-t", "--timeout"),
                {
                    "type": int,
                    "default": None,
                    "dest": "timeout",
                    "help": "Timeout in seconds for container shutdown",
                },
            ),
            (
                ("-V", "--renew-anon-volumes"),
                {
                    "action": "store_true",
                    "default": False,
                    "dest": "renew_anon_volumes",
                    "help": "Recreate anonymous volumes",
                },
            ),
            (
                "--wait",
                {
                    "action": "store_true",
                    "default": False,
                    "help": "Wait for services to be running|healthy",
                },
            ),
            (
                "--wait-timeout",
                {
                    "type": int,
                    "default": None,
                    "help": "Max duration to wait for services",
                },
            ),
            (
                "--no-deps",
                {
                    "action": "store_true",
                    "default": False,
                    "help": "Don't start linked services",
                },
            ),
            (
                "--no-start",
                {
                    "action": "store_true",
                    "default": False,
                    "help": "Don't start services after creating",
                },
            ),
            (
                "--menu",
                {
                    "action": "store_true",
                    "default": False,
                    "help": "Enable interactive shortcuts",
                },
            ),
            (
                ("-w", "--watch"),
                {
                    "action": "store_true",
                    "default": False,
                    "dest": "watch",
                    "help": "Watch source code and rebuild on change",
                },
            ),
            (
                ("-y", "--yes"),
                {
                    "action": "store_true",
                    "default": False,
                    "dest": "yes",
                    "help": "Assume yes to all prompts",
                },
            ),
        ],
    },
    {
        "name": "down",
        "help": "Stop and remove containers",
        "func": compose_down,
        "args": [
            (
                "--remove-orphans",
                {
                    "action": "store_true",
                    "default": False,
                    "help": "Remove containers for services not defined in the Compose file",
                },
            ),
            (
                "--rmi",
                {"choices": ["local", "all"], "default": None, "help": "Remove images"},
            ),
            (
                ("-t", "--timeout"),
                {
                    "type": int,
                    "default": 0,
                    "dest": "timeout",
                    "help": "Timeout in seconds for container shutdown",
                },
            ),
            (
                ("-v", "--volumes"),
                {
                    "action": "store_true",
                    "default": False,
                    "dest": "volumes",
                    "help": "Remove named volumes declared as external",
                },
            ),
        ],
    },
    {
        "name": "exec",
        "help": "Execute a command in a running service container",
        "func": compose_exec,
        "args": [
            ("service", {"help": "Service name"}),
            ("command", {"nargs": "*", "help": "Command to execute"}),
            (
                ("-d", "--detach"),
                {
                    "action": "store_true",
                    "default": False,
                    "dest": "detach",
                    "help": "Run in background",
                },
            ),
            (
                "--env",
                {
                    "action": "append",
                    "default": None,
                    "help": "Set environment variables",
                },
            ),
            (
                ("--index",),
                {
                    "type": int,
                    "default": 1,
                    "help": "Container index if service has multiple instances",
                },
            ),
            (
                ("-T", "--no-tty"),
                {
                    "action": "store_true",
                    "default": False,
                    "dest": "no_tty",
                    "help": "Disable pseudo-TTY allocation",
                },
            ),
            (
                "--privileged",
                {
                    "action": "store_true",
                    "default": False,
                    "help": "Give extended privileges",
                },
            ),
            (
                ("--user", "-u"),
                {
                    "default": None,
                    "dest": "user",
                    "help": "Username or UID",
                },
            ),
            (
                ("--workdir", "-w"),
                {
                    "default": None,
                    "dest": "workdir",
                    "help": "Working directory inside the container",
                },
            ),
        ],
    },
    {
        "name": "kill",
        "help": "Kill containers",
        "func": compose_kill,
        "args": [
            (
                ("-s", "--signal"),
                {
                    "default": None,
                    "dest": "signal",
                    "help": "Signal to send (default: SIGKILL)",
                },
            ),
        ],
    },
    {
        "name": "run",
        "help": "Run a one-off command in a new container",
        "func": compose_run,
        "args": [
            ("service", {"help": "Service name"}),
            ("command", {"nargs": "*", "help": "Command and arguments"}),
            (
                "--build",
                {
                    "action": "store_true",
                    "default": False,
                    "help": "Build images before starting",
                },
            ),
            (
                ("-d", "--detach"),
                {
                    "action": "store_true",
                    "default": False,
                    "dest": "detach",
                    "help": "Run in background",
                },
            ),
            (
                "--entrypoint",
                {
                    "default": None,
                    "help": "Override entrypoint",
                },
            ),
            (
                ("-e", "--env"),
                {
                    "action": "append",
                    "default": None,
                    "dest": "env",
                    "help": "Set environment variables",
                },
            ),
            (
                "--label",
                {
                    "action": "append",
                    "default": None,
                    "help": "Add metadata to container",
                },
            ),
            (
                ("--name",),
                {
                    "default": None,
                    "help": "Assign a name to the container",
                },
            ),
            (
                "--no-deps",
                {
                    "action": "store_true",
                    "default": False,
                    "help": "Don't start linked services",
                },
            ),
            (
                ("-p", "--publish"),
                {
                    "action": "append",
                    "default": None,
                    "dest": "publish",
                    "help": "Publish a port",
                },
            ),
            (
                ("-q", "--quiet"),
                {
                    "action": "store_true",
                    "default": False,
                    "dest": "quiet",
                    "help": "Suppress pull output",
                },
            ),
            (
                ("--rm",),
                {
                    "action": "store_true",
                    "default": False,
                    "dest": "remove",
                    "help": "Remove container after run",
                },
            ),
            (
                ("-u", "--user"),
                {
                    "default": None,
                    "dest": "user",
                    "help": "Run as this user",
                },
            ),
            (
                ("-v", "--volume"),
                {
                    "action": "append",
                    "default": None,
                    "dest": "volume",
                    "help": "Bind mount a volume",
                },
            ),
            (
                ("-w", "--workdir"),
                {
                    "default": None,
                    "dest": "workdir",
                    "help": "Working directory inside the container",
                },
            ),
        ],
    },
    {
        "name": "restart",
        "help": "Restart service containers (down + up)",
        "func": compose_restart,
        "args": [
            (
                "--no-deps",
                {
                    "action": "store_true",
                    "default": False,
                    "help": "Don't restart dependent services",
                },
            ),
            (
                ("-t", "--timeout"),
                {
                    "type": int,
                    "default": 0,
                    "dest": "timeout",
                    "help": "Timeout in seconds",
                },
            ),
        ],
    },
    {
        "name": "start",
        "help": "Start containers without daemon-reload",
        "func": compose_start,
        "args": [],
    },
    {
        "name": "stop",
        "help": "Stop containers without disabling them",
        "func": compose_stop,
        "args": [
            (
                ("-t", "--timeout"),
                {
                    "type": int,
                    "default": None,
                    "dest": "timeout",
                    "help": "Timeout in seconds for container shutdown",
                },
            ),
        ],
    },
    {
        "name": "build",
        "help": "Build or rebuild services",
        "func": compose_build,
        "args": [
            (
                "--build-arg",
                {"nargs": "*", "default": None, "help": "Set build-time variables"},
            ),
            ("--builder", {"default": None, "help": "Set builder to use"}),
            (
                "--check",
                {
                    "action": "store_true",
                    "default": False,
                    "help": "Check build configuration",
                },
            ),
            (
                ("-m", "--memory"),
                {
                    "default": None,
                    "dest": "memory",
                    "help": "Memory limit for build container",
                },
            ),
            (
                "--no-cache",
                {
                    "action": "store_true",
                    "default": False,
                    "help": "Don't use cache when building",
                },
            ),
            (
                "--print",
                {
                    "action": "store_true",
                    "default": False,
                    "help": "Print equivalent bake file",
                },
            ),
            (
                "--provenance",
                {
                    "action": "store_true",
                    "default": False,
                    "help": "Add provenance attestation",
                },
            ),
            (
                "--pull",
                {
                    "action": "store_true",
                    "default": False,
                    "help": "Always attempt to pull newer image",
                },
            ),
            (
                "--push",
                {
                    "action": "store_true",
                    "default": False,
                    "help": "Push service images",
                },
            ),
            (
                ("-q", "--quiet"),
                {
                    "action": "store_true",
                    "default": False,
                    "dest": "quiet",
                    "help": "Suppress build output",
                },
            ),
            (
                "--sbom",
                {
                    "action": "store_true",
                    "default": False,
                    "help": "Add SBOM attestation",
                },
            ),
            ("--ssh", {"default": None, "help": "SSH authentications for building"}),
            (
                "--with-dependencies",
                {
                    "action": "store_true",
                    "default": False,
                    "help": "Also build dependencies",
                },
            ),
        ],
    },
    {
        "name": "pull",
        "help": "Pull service images",
        "func": compose_pull,
        "args": [
            (
                "--ignore-buildable",
                {
                    "action": "store_true",
                    "default": False,
                    "help": "Skip images that can be built",
                },
            ),
            (
                "--ignore-pull-failures",
                {
                    "action": "store_true",
                    "default": False,
                    "help": "Continue on pull failure",
                },
            ),
            (
                "--include-deps",
                {
                    "action": "store_true",
                    "default": False,
                    "help": "Also pull dependencies",
                },
            ),
            (
                "--policy",
                {
                    "choices": ["missing", "always"],
                    "default": None,
                    "help": "Pull policy",
                },
            ),
            (
                ("-q", "--quiet"),
                {
                    "action": "store_true",
                    "default": False,
                    "dest": "quiet",
                    "help": "Suppress output",
                },
            ),
        ],
    },
    {
        "name": "ps",
        "help": "List containers",
        "func": compose_ps,
        "args": [
            (
                ("-a", "--all"),
                {
                    "action": "store_true",
                    "default": False,
                    "dest": "_all",
                    "help": "Show all containers",
                },
            ),
            (
                "--filter",
                {
                    "choices": [
                        "paused",
                        "restarting",
                        "removing",
                        "running",
                        "dead",
                        "created",
                        "exited",
                    ],
                    "default": None,
                    "dest": "_filter",
                    "help": "Filter containers by status",
                },
            ),
            (
                "--format",
                {
                    "choices": ["pretty", "json"],
                    "default": "pretty",
                    "dest": "_format",
                    "help": "Output format",
                },
            ),
            (
                "--no-trunc",
                {
                    "action": "store_true",
                    "default": False,
                    "help": "Don't truncate output",
                },
            ),
            (
                "--orphans",
                {
                    "action": "store_true",
                    "default": True,
                    "help": "Include orphaned containers",
                },
            ),
            (
                ("-q", "--quiet"),
                {
                    "action": "store_true",
                    "default": False,
                    "dest": "quiet",
                    "help": "Only display IDs",
                },
            ),
            (
                "--services",
                {"action": "store_true", "default": False, "help": "Display services"},
            ),
            (
                "--status",
                {
                    "choices": [
                        "paused",
                        "restarting",
                        "removing",
                        "running",
                        "dead",
                        "created",
                        "exited",
                    ],
                    "default": None,
                    "help": "Filter by status",
                },
            ),
        ],
    },
    {
        "name": "logs",
        "help": "View output from containers",
        "func": compose_logs,
        "args": [
            (
                ("-f", "--follow"),
                {
                    "action": "store_true",
                    "default": False,
                    "dest": "follow",
                    "help": "Follow log output",
                },
            ),
            ("--index", {"type": int, "default": 0, "help": "Index of the container"}),
            (
                "--no-color",
                {
                    "action": "store_true",
                    "default": False,
                    "help": "Produce monochrome output",
                },
            ),
            (
                "--no-log-prefix",
                {
                    "action": "store_true",
                    "default": False,
                    "help": "Don't print prefix in logs",
                },
            ),
            (
                "--since",
                {"default": 0, "help": "Show logs since timestamp or relative time"},
            ),
            (
                "--tail",
                {
                    "type": int,
                    "default": None,
                    "help": "Number of lines to show from end",
                },
            ),
            (
                ("-t", "--timestamps"),
                {
                    "action": "store_true",
                    "default": False,
                    "dest": "timestamps",
                    "help": "Show timestamps",
                },
            ),
            (
                "--until",
                {"default": 0, "help": "Show logs before timestamp or relative time"},
            ),
        ],
    },
    {
        "name": "top",
        "help": "Display running processes",
        "func": compose_top,
        "args": [
            ("services", {"nargs": "*", "help": "Services to display"}),
        ],
    },
    {
        "name": "images",
        "help": "List images",
        "func": compose_images,
        "args": [
            (
                "--format",
                {
                    "choices": ["table", "json"],
                    "default": "table",
                    "dest": "_format",
                    "help": "Output format",
                },
            ),
            (
                ("-q", "--quiet"),
                {
                    "action": "store_true",
                    "default": False,
                    "dest": "quiet",
                    "help": "Only display image IDs",
                },
            ),
        ],
    },
    {
        "name": "port",
        "help": "Print the public port for a port binding",
        "func": compose_port,
        "args": [
            ("service", {"help": "Service name"}),
            ("private_port", {"type": int, "nargs": "?", "help": "Private port"}),
            (
                "--protocol",
                {
                    "choices": ["tcp", "udp"],
                    "default": "tcp",
                    "help": "Protocol (tcp or udp)",
                },
            ),
            ("--index", {"type": int, "default": 1, "help": "Index of the container"}),
        ],
    },
    {
        "name": "config",
        "help": "Validate and view compose config",
        "func": compose_config,
        "args": [
            (
                "--format",
                {
                    "choices": ["yaml", "json"],
                    "default": "yaml",
                    "dest": "_format",
                    "help": "Output format",
                },
            ),
            (
                "--environment",
                {
                    "action": "store_true",
                    "default": False,
                    "help": "Print environment used for interpolation",
                },
            ),
            ("--hash", {"default": None, "help": "Print service config hash"}),
            (
                "--images",
                {"action": "store_true", "default": False, "help": "Print image names"},
            ),
            (
                "--lock-image-digests",
                {
                    "action": "store_true",
                    "default": False,
                    "help": "Produce override with image digests",
                },
            ),
            (
                "--models",
                {"action": "store_true", "default": False, "help": "Print model names"},
            ),
            (
                "--networks",
                {
                    "action": "store_true",
                    "default": False,
                    "help": "Print network names",
                },
            ),
            (
                "--no-consistency",
                {
                    "action": "store_true",
                    "default": False,
                    "help": "Don't check model consistency",
                },
            ),
            (
                "--no-env-resolution",
                {
                    "action": "store_true",
                    "default": False,
                    "help": "Don't resolve env files",
                },
            ),
            (
                "--no-interpolate",
                {
                    "action": "store_true",
                    "default": False,
                    "help": "Don't interpolate environment variables",
                },
            ),
            (
                "--no-normalize",
                {
                    "action": "store_true",
                    "default": False,
                    "help": "Don't normalize compose model",
                },
            ),
            (
                "--no-path-resolution",
                {
                    "action": "store_true",
                    "default": False,
                    "help": "Don't resolve file paths",
                },
            ),
            (
                ("-o", "--output"),
                {"default": None, "dest": "output", "help": "Save to file"},
            ),
            (
                "--profiles",
                {
                    "action": "store_true",
                    "default": False,
                    "help": "Print profile names",
                },
            ),
            (
                ("-q", "--quiet"),
                {
                    "action": "store_true",
                    "default": False,
                    "dest": "quiet",
                    "help": "Only validate, don't print",
                },
            ),
            (
                "--resolve-image-digests",
                {
                    "action": "store_true",
                    "default": False,
                    "help": "Pin image tags to digests",
                },
            ),
            (
                "--services",
                {
                    "action": "store_true",
                    "default": False,
                    "help": "Print service names",
                },
            ),
            (
                "--variables",
                {
                    "action": "store_true",
                    "default": False,
                    "help": "Print model variables",
                },
            ),
            (
                "--volumes",
                {
                    "action": "store_true",
                    "default": False,
                    "help": "Print volume names",
                },
            ),
        ],
    },
    {
        "name": "convert",
        "help": "Preview quadlet files",
        "func": compose_convert,
        "args": [
            (
                "--format",
                {
                    "choices": ["yaml", "json"],
                    "default": "yaml",
                    "dest": "_format",
                    "help": "Output format",
                },
            ),
            (
                "--hash",
                {
                    "action": "store_true",
                    "default": False,
                    "help": "Print service config hash",
                },
            ),
            (
                "--images",
                {"action": "store_true", "default": False, "help": "Print image names"},
            ),
            (
                "--no-consistency",
                {
                    "action": "store_true",
                    "default": False,
                    "help": "Don't check model consistency",
                },
            ),
            (
                "--no-interpolate",
                {
                    "action": "store_true",
                    "default": False,
                    "help": "Don't interpolate environment variables",
                },
            ),
            (
                "--no-normalize",
                {
                    "action": "store_true",
                    "default": False,
                    "help": "Don't normalize compose model",
                },
            ),
            (
                ("-o", "--output"),
                {"default": None, "dest": "output", "help": "Save to file"},
            ),
            (
                "--profiles",
                {
                    "action": "store_true",
                    "default": False,
                    "help": "Print profile names",
                },
            ),
            (
                ("-q", "--quiet"),
                {
                    "action": "store_true",
                    "default": False,
                    "dest": "quiet",
                    "help": "Only validate, don't print",
                },
            ),
            (
                "--resolve-image-digests",
                {
                    "action": "store_true",
                    "default": False,
                    "help": "Pin image tags to digests",
                },
            ),
            (
                "--services",
                {
                    "action": "store_true",
                    "default": False,
                    "help": "Print service names",
                },
            ),
            (
                "--volumes",
                {
                    "action": "store_true",
                    "default": False,
                    "help": "Print volume names",
                },
            ),
        ],
    },
    {
        "name": "version",
        "help": "Show version information",
        "func": compose_version,
        "args": [
            (
                ("-f", "--format"),
                {
                    "choices": ["pretty", "json"],
                    "default": "pretty",
                    "dest": "_format",
                    "help": "Output format",
                },
            ),
            (
                "--short",
                {
                    "action": "store_true",
                    "default": False,
                    "help": "Show only version number",
                },
            ),
        ],
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
    except ValueError as e:
        console = Console(stderr=True)
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
