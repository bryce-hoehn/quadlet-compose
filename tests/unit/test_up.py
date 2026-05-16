"""Tests for subcommands/up.py helper functions."""

import os
from pathlib import Path

import pytest

from models.quadlet.container import ContainerUnit
from models.quadlet.pod import PodUnit
from utils.mapping import QuadletBundle

from subcommands.up import _create_bind_mount_dirs


class TestCreateBindMountDirs:
    """Tests for _create_bind_mount_dirs()."""

    def test_creates_bind_mount_host_dir(self, tmp_path: Path) -> None:
        """Absolute-path bind mounts are created on the host."""
        host_dir = tmp_path / "data"
        container = ContainerUnit(
            Image="nginx:latest",
            Volume=[f"{host_dir}/html:/usr/share/nginx/html"],
        )
        bundle = QuadletBundle(containers=[container])

        _create_bind_mount_dirs(bundle)

        assert host_dir.joinpath("html").is_dir()

    def test_creates_nested_bind_mount_dirs(self, tmp_path: Path) -> None:
        """Deeply nested bind mount paths are created in one shot."""
        host_dir = tmp_path / "a" / "b" / "c"
        container = ContainerUnit(
            Image="nginx:latest",
            Volume=[f"{host_dir}:/data"],
        )
        bundle = QuadletBundle(containers=[container])

        _create_bind_mount_dirs(bundle)

        assert host_dir.is_dir()

    def test_skips_named_volumes(self) -> None:
        """Named volumes (no leading /) are not created as directories."""
        container = ContainerUnit(
            Image="nginx:latest",
            Volume=["mydata:/data"],
        )
        bundle = QuadletBundle(containers=[container])

        # Should not raise — named volumes don't start with /
        _create_bind_mount_dirs(bundle)

    def test_skips_containers_without_volumes(self) -> None:
        """Containers with no Volume field are silently skipped."""
        container = ContainerUnit(Image="nginx:latest")
        bundle = QuadletBundle(containers=[container])

        _create_bind_mount_dirs(bundle)  # should not raise

    def test_skips_empty_volume_list(self) -> None:
        """Containers with an empty Volume list are silently skipped."""
        container = ContainerUnit(Image="nginx:latest", Volume=[])
        bundle = QuadletBundle(containers=[container])

        _create_bind_mount_dirs(bundle)  # should not raise

    def test_existing_dir_not_an_error(self, tmp_path: Path) -> None:
        """Pre-existing directories are left untouched (exist_ok=True)."""
        host_dir = tmp_path / "already"
        host_dir.mkdir()
        container = ContainerUnit(
            Image="nginx:latest",
            Volume=[f"{host_dir}:/data"],
        )
        bundle = QuadletBundle(containers=[container])

        _create_bind_mount_dirs(bundle)

        assert host_dir.is_dir()

    def test_multiple_volumes_multiple_containers(self, tmp_path: Path) -> None:
        """All bind mount dirs across all containers are created."""
        dir_a = tmp_path / "a"
        dir_b = tmp_path / "b"
        dir_c = tmp_path / "c"
        bundle = QuadletBundle(
            containers=[
                ContainerUnit(
                    Image="app:latest",
                    Volume=[
                        f"{dir_a}:/app/data",
                        f"{dir_b}:/app/config",
                        "named_vol:/app/logs",
                    ],
                ),
                ContainerUnit(
                    Image="db:latest",
                    Volume=[f"{dir_c}:/var/lib/db"],
                ),
            ],
        )

        _create_bind_mount_dirs(bundle)

        assert dir_a.is_dir()
        assert dir_b.is_dir()
        assert dir_c.is_dir()

    def test_bundle_with_no_containers(self) -> None:
        """A bundle with no containers at all is handled gracefully."""
        bundle = QuadletBundle(pod=PodUnit(PodName="empty"))

        _create_bind_mount_dirs(bundle)  # should not raise

    def test_volume_with_options(self, tmp_path: Path) -> None:
        """Bind mounts with :ro or other options still extract the host path."""
        host_dir = tmp_path / "readonly"
        container = ContainerUnit(
            Image="nginx:latest",
            Volume=[f"{host_dir}:/usr/share/nginx/html:ro"],
        )
        bundle = QuadletBundle(containers=[container])

        _create_bind_mount_dirs(bundle)

        assert host_dir.is_dir()
