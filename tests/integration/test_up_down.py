"""Integration tests for podlet-compose up and down commands.

Requires: podman, podlet, and systemd user session.
Run with: pytest -m integration tests/integration/test_up_down.py
"""

import subprocess
import time

import pytest

from tests.conftest import PROJECT_ROOT

pytestmark = pytest.mark.integration

PODLET_COMPOSE = str(PROJECT_ROOT / "podlet_compose.py")
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


def _cleanup(compose_file):
    """Best-effort cleanup — don't fail if down doesn't work."""
    subprocess.run(
        ["python", PODLET_COMPOSE, "-f", compose_file, "down"],
        capture_output=True,
        text=True,
        timeout=30,
    )


class TestUpDown:
    """Test podlet-compose up and down lifecycle."""

    compose_file = str(FIXTURES / "up_down" / "compose.yaml")

    def test_up_creates_running_containers(self):
        """podlet-compose up -d should create containers visible via podman ps."""
        try:
            _run(["python", PODLET_COMPOSE, "-f", self.compose_file, "up", "-d"])
            time.sleep(5)  # Wait for systemd to start containers

            result = _run(["podman", "ps", "--format", "{{.Names}}"])
            names = result.stdout.strip()
            assert "test-compose-web" in names or "test-compose-db" in names, (
                f"Expected container names in podman ps output, got: {names}"
            )
        finally:
            _cleanup(self.compose_file)

    def test_down_removes_containers(self):
        """podlet-compose down should remove containers."""
        _run(["python", PODLET_COMPOSE, "-f", self.compose_file, "up", "-d"])
        time.sleep(5)

        # Verify containers exist before down
        _run(["podman", "container", "exists", "test-compose-web"])

        # Down
        _run(["python", PODLET_COMPOSE, "-f", self.compose_file, "down"])
        time.sleep(3)

        # Verify containers are gone
        _run(["podman", "container", "exists", "test-compose-web"], expected_rc=1)

    def test_up_with_volumes(self):
        """podlet-compose up with named volumes should create podman volumes."""
        compose_file = str(FIXTURES / "volumes" / "compose.yaml")
        try:
            _run(["python", PODLET_COMPOSE, "-f", compose_file, "up", "-d"])
            time.sleep(5)

            result = _run(["podman", "volume", "exists", "pgdata"])
            assert result.returncode == 0, "Expected volume 'pgdata' to exist"
        finally:
            _cleanup(compose_file)

    def test_up_with_networks(self):
        """podlet-compose up with networks should create podman networks."""
        compose_file = str(FIXTURES / "networks" / "compose.yaml")
        try:
            _run(["python", PODLET_COMPOSE, "-f", compose_file, "up", "-d"])
            time.sleep(5)

            result = _run(["podman", "ps", "--format", "{{.Names}}"])
            names = result.stdout.strip()
            assert "networks-test-web" in names or "networks-test-app" in names
        finally:
            _cleanup(compose_file)

    def test_up_empty_services_no_error(self):
        """podlet-compose up with empty services should not crash."""
        compose_file = str(FIXTURES / "empty_services" / "compose.yaml")
        _run(["python", PODLET_COMPOSE, "-f", compose_file, "up", "-d"])

    def test_up_creates_bind_mount_dirs(self):
        """podlet-compose up should auto-create missing bind mount host directories."""
        compose_file = str(FIXTURES / "bind_mounts" / "compose.yaml")
        fixture_dir = FIXTURES / "bind_mounts"
        html_dir = fixture_dir / "html"
        try:
            assert not html_dir.exists(), "html dir should not exist before test"
            _run(["python", PODLET_COMPOSE, "-f", compose_file, "up", "-d"])
            assert html_dir.is_dir(), "_ensure_bind_mount_dirs should have created html dir"
            time.sleep(5)
            result = _run(["podman", "ps", "--format", "{{.Names}}"])
            assert "bindmount-test-web" in result.stdout.strip()
        finally:
            _cleanup(compose_file)
            if html_dir.exists():
                html_dir.rmdir()
