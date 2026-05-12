"""Integration tests for quadlet-compose config command.

Requires: podman, podlet, and systemd user session.
Run with: pytest -m integration tests/integration/test_config.py
"""

import subprocess

import pytest

from tests.conftest import PROJECT_ROOT

pytestmark = pytest.mark.integration

QUADLET_COMPOSE = str(PROJECT_ROOT / "quadlet_compose.py")
FIXTURES = PROJECT_ROOT / "tests" / "integration" / "fixtures"


def _run(args, expected_rc=0, timeout=30):
    """Run a command, assert return code, return CompletedProcess."""
    result = subprocess.run(
        args,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode != expected_rc:
        pytest.fail(
            f"Command {args} returned {result.returncode}, expected {expected_rc}\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
    return result


class TestConfigCommand:
    """Test quadlet-compose config command output."""

    def test_config_shows_project_name(self):
        compose_file = str(FIXTURES / "up_down" / "compose.yaml")
        result = _run(["python", QUADLET_COMPOSE, "-f", compose_file, "config"])
        assert "name: test-compose" in result.stdout

    def test_config_shows_service_names(self):
        compose_file = str(FIXTURES / "networks" / "compose.yaml")
        result = _run(["python", QUADLET_COMPOSE, "-f", compose_file, "config"])
        assert "web" in result.stdout
        assert "app" in result.stdout

    def test_config_shows_volumes(self):
        compose_file = str(FIXTURES / "volumes" / "compose.yaml")
        result = _run(["python", QUADLET_COMPOSE, "-f", compose_file, "config"])
        assert "volumes:" in result.stdout
        assert "pgdata" in result.stdout

    def test_config_shows_networks(self):
        compose_file = str(FIXTURES / "networks" / "compose.yaml")
        result = _run(["python", QUADLET_COMPOSE, "-f", compose_file, "config"])
        assert "networks:" in result.stdout
        assert "frontend" in result.stdout
        assert "backend" in result.stdout

    def test_config_empty_services(self):
        compose_file = str(FIXTURES / "empty_services" / "compose.yaml")
        result = _run(["python", QUADLET_COMPOSE, "-f", compose_file, "config"])
        assert "name: empty-services" in result.stdout
