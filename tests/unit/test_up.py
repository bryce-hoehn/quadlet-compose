"""Tests for utils/_helpers.py helpers and subcommands/up.py."""

from pathlib import Path
from unittest.mock import patch

from models.quadlet.container import ContainerUnit
from utils._helpers import extract_hash, quadlet_to_service
from utils.mapping import QuadletBundle


# ---------------------------------------------------------------------------
# _quadlet_to_service
# ---------------------------------------------------------------------------


class TestQuadletToService:
    """Tests for quadlet_to_service filename→service name mapping."""

    def test_container(self) -> None:
        assert quadlet_to_service("web.container") == "web.service"

    def test_pod(self) -> None:
        assert quadlet_to_service("myapp.pod") == "myapp-pod.service"

    def test_network(self) -> None:
        assert quadlet_to_service("frontend.network") == "frontend-network.service"

    def test_volume(self) -> None:
        assert quadlet_to_service("data.volume") == "data-volume.service"

    def test_build(self) -> None:
        assert quadlet_to_service("myapp-web.build") == "myapp-web-build.service"


# ---------------------------------------------------------------------------
# _extract_hash
# ---------------------------------------------------------------------------


class TestExtractHash:
    """Tests for extract_hash label extraction."""

    def test_extracts_hash_from_content(self) -> None:
        content = (
            "[Container]\n"
            "Image=nginx:latest\n"
            "Label=io.quadlet-compose.hash=abc123def456"
        )
        assert extract_hash(content) == "abc123def456"

    def test_returns_none_when_no_hash(self) -> None:
        content = "[Container]\nImage=nginx:latest"
        assert extract_hash(content) is None

    def test_returns_none_for_empty_string(self) -> None:
        assert extract_hash("") is None

    def test_extracts_full_sha256_hex(self) -> None:
        digest = "a" * 64
        content = (
            f"[Container]\nImage=nginx:latest\nLabel=io.quadlet-compose.hash={digest}"
        )
        assert extract_hash(content) == digest

    def test_ignores_partial_label_match(self) -> None:
        """A label that contains but doesn't start with the prefix is ignored."""
        content = (
            "[Container]\n"
            "Image=nginx:latest\n"
            "Label=prefix-io.quadlet-compose.hash=abc123"
        )
        assert extract_hash(content) is None

    def test_finds_hash_among_other_labels(self) -> None:
        content = (
            "[Container]\n"
            "Image=nginx:latest\n"
            "Label=io.quadlet-compose.project=myapp\n"
            "Label=io.quadlet-compose.hash=deadbeef"
        )
        assert extract_hash(content) == "deadbeef"


# ---------------------------------------------------------------------------
# _ensure_bind_mount_dirs
# ---------------------------------------------------------------------------


class TestEnsureBindMountDirs:
    """Tests for _ensure_bind_mount_dirs in subcommands/up.py."""

    @staticmethod
    def _make_container(volumes: list[str] | None) -> ContainerUnit:
        """Build a minimal ContainerUnit with the given Volume entries."""
        return ContainerUnit(
            Image="nginx:latest",
            ContainerName="test-web",
            Volume=volumes,
        )

    def test_creates_missing_directory(self, tmp_path: Path) -> None:
        bind_src = tmp_path / "data"
        container = self._make_container([f"{bind_src}:/app/data"])
        bundle = QuadletBundle(containers=[container])

        from subcommands.up import _ensure_bind_mount_dirs

        _ensure_bind_mount_dirs(bundle)

        assert bind_src.is_dir()

    def test_creates_parent_for_file_like_path(self, tmp_path: Path) -> None:
        """Paths with a suffix (e.g. .env, .yml) are treated as file targets."""
        bind_src = tmp_path / "config" / "app.yml"
        container = self._make_container([f"{bind_src}:/app/config.yml"])
        bundle = QuadletBundle(containers=[container])

        from subcommands.up import _ensure_bind_mount_dirs

        _ensure_bind_mount_dirs(bundle)

        # Parent directory should exist, but the file itself should NOT.
        assert bind_src.parent.is_dir()
        assert not bind_src.exists()

    def test_skips_named_volumes(self, tmp_path: Path) -> None:
        """Named volumes (no leading ``/``) are not created on the host."""
        container = self._make_container(["mydata:/app/data"])
        bundle = QuadletBundle(containers=[container])

        from subcommands.up import _ensure_bind_mount_dirs

        _ensure_bind_mount_dirs(bundle)

        # Nothing to assert — just ensure no exception or file creation.
        assert not (tmp_path / "mydata").exists()

    def test_skips_existing_paths(self, tmp_path: Path) -> None:
        bind_src = tmp_path / "already_exists"
        bind_src.mkdir()
        container = self._make_container([f"{bind_src}:/app/data"])
        bundle = QuadletBundle(containers=[container])

        from subcommands.up import _ensure_bind_mount_dirs

        _ensure_bind_mount_dirs(bundle)

        # Directory already existed; no error.
        assert bind_src.is_dir()

    def test_handles_none_volume(self) -> None:
        """Containers with Volume=None should be silently skipped."""
        container = self._make_container(None)
        bundle = QuadletBundle(containers=[container])

        from subcommands.up import _ensure_bind_mount_dirs

        _ensure_bind_mount_dirs(bundle)  # should not raise

    def test_handles_empty_volume_list(self) -> None:
        """Containers with an empty Volume list should be silently skipped."""
        container = self._make_container([])
        bundle = QuadletBundle(containers=[container])

        from subcommands.up import _ensure_bind_mount_dirs

        _ensure_bind_mount_dirs(bundle)  # should not raise

    def test_creates_nested_directories(self, tmp_path: Path) -> None:
        """Deeply nested bind mount paths are created with parents=True."""
        bind_src = tmp_path / "a" / "b" / "c" / "data"
        container = self._make_container([f"{bind_src}:/app/data"])
        bundle = QuadletBundle(containers=[container])

        from subcommands.up import _ensure_bind_mount_dirs

        _ensure_bind_mount_dirs(bundle)

        assert bind_src.is_dir()

    def test_mixed_volumes(self, tmp_path: Path) -> None:
        """Bind mounts are created; named volumes are skipped."""
        bind_src = tmp_path / "host_data"
        container = self._make_container(
            [
                f"{bind_src}:/app/data",
                "named_vol:/app/vol",
            ]
        )
        bundle = QuadletBundle(containers=[container])

        from subcommands.up import _ensure_bind_mount_dirs

        _ensure_bind_mount_dirs(bundle)

        assert bind_src.is_dir()

    def test_multiple_containers(self, tmp_path: Path) -> None:
        """All containers in the bundle are processed."""
        src_a = tmp_path / "data_a"
        src_b = tmp_path / "data_b"
        bundle = QuadletBundle(
            containers=[
                self._make_container([f"{src_a}:/a"]),
                self._make_container([f"{src_b}:/b"]),
            ]
        )

        from subcommands.up import _ensure_bind_mount_dirs

        _ensure_bind_mount_dirs(bundle)

        assert src_a.is_dir()
        assert src_b.is_dir()
