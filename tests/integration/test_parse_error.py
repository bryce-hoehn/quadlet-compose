"""Integration tests for quadlet-compose error handling on malformed YAML.

Requires: podman, podlet, and systemd user session.
Run with: pytest -m integration tests/integration/test_parse_error.py
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


class TestParseError:
    """Test quadlet-compose behavior with malformed YAML files."""

    def test_malformed_yaml_returns_nonzero(self):
        bad_file = str(FIXTURES / "parse_error" / "compose-error.yaml")
        result = subprocess.run(
            ["python", QUADLET_COMPOSE, "-f", bad_file, "config"],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0, "Expected non-zero exit code for malformed YAML"

    def test_valid_yaml_succeeds(self):
        good_file = str(FIXTURES / "up_down" / "compose.yaml")
        _run(["python", QUADLET_COMPOSE, "-f", good_file, "config"])
