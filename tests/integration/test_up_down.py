"""Integration tests for quadlet-compose up and down commands.

Requires: podman, podlet, and systemd user session.
Run with: pytest -m integration tests/integration/test_up_down.py
"""

import subprocess
import time

import pytest

from tests.conftest import PROJECT_ROOT

pytestmark = pytest.mark.integration

QUADLET_COMPOSE = str(PROJECT_ROOT / "quadlet_compose.py")
FIXTURES = PROJECT_ROOT / "tests" / "integration" / "fixtures"


def _run(args, expected_rc=0, timeout=60):
    """Run a command, assert return code, return CompletedProcess."""
    result = subprocess.run(
        args,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if expected_rc is not None and result.returncode != expected_rc:
        pytest.fail(
            f"Command {args} returned {result.returncode}, expected {expected_rc}\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
    return result


def _wait_for_container(name, timeout=30):
    """Poll until a container exists, raising on timeout."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        result = subprocess.run(
            ["podman", "container", "exists", name],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return
        time.sleep(1)
    pytest.fail(f"Container {name} did not appear within {timeout}s")


def _cleanup(compose_file):
    """Best-effort cleanup — don't fail if down doesn't work."""
    subprocess.run(
        ["python", QUADLET_COMPOSE, "-f", compose_file, "down"],
        capture_output=True,
        text=True,
        timeout=30,
    )


class TestUpDown:
    """Test quadlet-compose up and down lifecycle."""

    compose_file = str(FIXTURES / "up_down" / "compose.yaml")

    def test_up_creates_running_containers(self):
        """quadlet-compose up -d should create containers visible via podman ps."""
        try:
            _run(["python", QUADLET_COMPOSE, "-f", self.compose_file, "up", "-d"])
            _wait_for_container("systemd-test-compose-web")

            result = _run(["podman", "ps", "--format", "{{.Names}}"])
            names = result.stdout.strip()
            assert (
                "test-compose-web" in names
            ), f"Expected container names in podman ps output, got: {names}"
        finally:
            _cleanup(self.compose_file)

    def test_down_removes_containers(self):
        """quadlet-compose down should remove containers."""
        try:
            _run(["python", QUADLET_COMPOSE, "-f", self.compose_file, "up", "-d"])
            _wait_for_container("systemd-test-compose-web")

            # Down
            _run(["python", QUADLET_COMPOSE, "-f", self.compose_file, "down"])
            time.sleep(3)

            # Verify containers are gone
            _run(
                ["podman", "container", "exists", "systemd-test-compose-web"],
                expected_rc=1,
            )
        finally:
            _cleanup(self.compose_file)

    def test_up_with_volumes(self):
        """quadlet-compose up with named volumes should create podman volumes."""
        compose_file = str(FIXTURES / "volumes" / "compose.yaml")
        try:
            _run(["python", QUADLET_COMPOSE, "-f", compose_file, "up", "-d"])
            _wait_for_container("systemd-volumes-test-db")

            result = _run(["podman", "volume", "exists", "pgdata"])
            assert result.returncode == 0, "Expected volume 'pgdata' to exist"
        finally:
            _cleanup(compose_file)

    def test_up_with_networks(self):
        """quadlet-compose up with networks should create podman networks."""
        compose_file = str(FIXTURES / "networks" / "compose.yaml")
        try:
            _run(["python", QUADLET_COMPOSE, "-f", compose_file, "up", "-d"])
            _wait_for_container("systemd-networks-test-web")

            result = _run(["podman", "ps", "--format", "{{.Names}}"])
            names = result.stdout.strip()
            assert "networks-test-web" in names or "networks-test-app" in names
        finally:
            _cleanup(compose_file)

    def test_up_empty_services_no_error(self):
        """quadlet-compose up with empty services should not crash."""
        compose_file = str(FIXTURES / "empty_services" / "compose.yaml")
        _run(["python", QUADLET_COMPOSE, "-f", compose_file, "up", "-d"])

    def test_up_creates_bind_mount_dirs(self):
        """quadlet-compose up should auto-create missing bind mount host directories."""
        compose_file = str(FIXTURES / "bind_mounts" / "compose.yaml")
        fixture_dir = FIXTURES / "bind_mounts"
        html_dir = fixture_dir / "html"
        try:
            assert not html_dir.exists(), "html dir should not exist before test"
            _run(["python", QUADLET_COMPOSE, "-f", compose_file, "up", "-d"])
            assert (
                html_dir.is_dir()
            ), "_ensure_bind_mount_dirs should have created html dir"
            _wait_for_container("systemd-bindmount-test-web")
            result = _run(["podman", "ps", "--format", "{{.Names}}"])
            assert "bindmount-test-web" in result.stdout.strip()
        finally:
            _cleanup(compose_file)
            if html_dir.exists():
                html_dir.rmdir()
