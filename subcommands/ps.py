"""compose ps command — list containers."""

import json
import subprocess

from typing import Literal
from rich.console import Console
from rich.table import Table

from utils import run_cmd
from utils.compose import get_service_info, parse_compose, resolve_compose_path

HELP = "List containers"
ARGS = [
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
]


def compose_ps(
    *,
    compose_file: str | None = None,
    _all: bool = False,
    _filter: (
        Literal[
            "paused", "restarting", "removing", "running", "dead", "created", "exited"
        ]
        | None
    ) = None,
    _format: Literal["pretty", "json"] = "pretty",
    no_trunc: bool = False,
    orphans: bool = True,
    quiet: bool = False,
    services: bool = False,
    status: (
        Literal[
            "paused", "restarting", "removing", "running", "dead", "created", "exited"
        ]
        | None
    ) = None,
) -> None:
    """List containers."""

    compose_path = resolve_compose_path(compose_file)
    compose = parse_compose(compose_path)

    info = get_service_info(compose, compose_path=compose_path)

    if services:
        for name in info.container_names.values():
            print(name)
        return

    containers = list(info.container_names.values())

    args = ["podman", "ps"]

    if _all:
        args.append("-a")
    if _filter:
        args.extend(["--filter", f"status={_filter}"])
    if status:
        args.extend(["--filter", f"status={status}"])
    if quiet:
        args.append("-q")
    if no_trunc:
        args.append("--no-trunc")

    label = f"io.quadlet-compose.project={info.project_name}"
    args.extend(["--filter", f"label={label}"])

    if _format == "json":
        args.extend(["--format", "json"])
        result = run_cmd(args, capture_output=True, text=True)
        if result.stdout.strip():
            for line in result.stdout.strip().split("\n"):
                data = json.loads(line)
                print(json.dumps(data))
        return

    run_cmd(args)
