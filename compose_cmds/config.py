"""compose_config - Validate and view compose configuration."""

import sys

from ruamel.yaml import YAML

from utils import resolve_compose_path, parse_compose


def compose_config(compose_file: str | None = None, **_kwargs) -> None:
    """Validate and display the parsed compose configuration.

    Parses the compose file, validates its structure, and prints the
    normalized configuration including derived metadata like project name
    and service names.
    """
    compose_path = resolve_compose_path(compose_file)
    compose_data = parse_compose(compose_path)

    ryaml = YAML()
    with open(compose_path, encoding="utf-8") as f:
        raw = ryaml.load(f)

    print(f"name: {compose_data['project']}")
    print(f"services: [{', '.join(compose_data['service_names'])}]")
    if compose_data["volume_names"]:
        print(f"volumes: [{', '.join(compose_data['volume_names'])}]")
    if compose_data["network_names"]:
        print(f"networks: [{', '.join(compose_data['network_names'])}]")
    print()
    ryaml.dump(raw, sys.stdout)
