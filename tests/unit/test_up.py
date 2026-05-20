"""Tests for utils/_helpers.py helpers and subcommands/up.py."""

from unittest.mock import MagicMock, patch

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
    """Tests for _ensure_bind_mount_dirs in subcommands/up.py.

    Uses mocked ``Path`` with Unix-style absolute paths so the tests
    work correctly on Windows (where ``C:\\path`` colons would collide
    with the volume ``src:target`` split and ``Path.is_absolute()``
    behaves differently).
    """

    @staticmethod
    def _make_container(volumes: list[str] | None) -> ContainerUnit:
        """Build a minimal ContainerUnit with the given Volume entries."""
        return ContainerUnit(
            Image="nginx:latest",
            ContainerName="test-web",
            Volume=volumes,
        )

    @patch("subcommands.up.Path")
    def test_creates_missing_directory(self, mock_path_cls: MagicMock) -> None:
        """Creates a missing bind mount source directory."""
        mock_path = MagicMock()
        mock_path.is_absolute.return_value = True
        mock_path.exists.return_value = False
        mock_path.suffix = ""
        mock_path_cls.return_value = mock_path

        container = self._make_container(["/tmp/testdata/data:/app/data"])
        bundle = QuadletBundle(containers=[container])

        from subcommands.up import _ensure_bind_mount_dirs

        _ensure_bind_mount_dirs(bundle)

        mock_path.mkdir.assert_called_once_with(parents=True, exist_ok=True)

    @patch("subcommands.up.Path")
    def test_creates_parent_for_file_like_path(self, mock_path_cls: MagicMock) -> None:
        """Paths with a suffix (e.g. .yml) only create the parent directory."""
        mock_path = MagicMock()
        mock_path.is_absolute.return_value = True
        mock_path.exists.return_value = False
        mock_path.suffix = ".yml"
        mock_path_cls.return_value = mock_path

        container = self._make_container(["/opt/config/app.yml:/app/config.yml"])
        bundle = QuadletBundle(containers=[container])

        from subcommands.up import _ensure_bind_mount_dirs

        _ensure_bind_mount_dirs(bundle)

        mock_path.parent.mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_path.mkdir.assert_not_called()

    @patch("subcommands.up.Path")
    def test_skips_named_volumes(self, mock_path_cls: MagicMock) -> None:
        """Named volumes (bare names) are not created on the host."""
        mock_path = MagicMock()
        mock_path.is_absolute.return_value = False
        mock_path_cls.return_value = mock_path

        container = self._make_container(["mydata:/app/data"])
        bundle = QuadletBundle(containers=[container])

        from subcommands.up import _ensure_bind_mount_dirs

        _ensure_bind_mount_dirs(bundle)

        mock_path.mkdir.assert_not_called()

    @patch("subcommands.up.Path")
    def test_skips_existing_paths(self, mock_path_cls: MagicMock) -> None:
        """Existing directories are left as-is (no mkdir call)."""
        mock_path = MagicMock()
        mock_path.is_absolute.return_value = True
        mock_path.exists.return_value = True
        mock_path_cls.return_value = mock_path

        container = self._make_container(["/tmp/already_exists:/app/data"])
        bundle = QuadletBundle(containers=[container])

        from subcommands.up import _ensure_bind_mount_dirs

        _ensure_bind_mount_dirs(bundle)

        mock_path.mkdir.assert_not_called()

    def test_handles_none_volume(self) -> None:
        """Containers with Volume=None should be silently skipped."""
        container = self._make_container(None)
        bundle = QuadletBundle(containers=[container])

        from subcommands.up import _ensure_bind_mount_dirs

        with patch("subcommands.up.Path") as mock_path_cls:
            _ensure_bind_mount_dirs(bundle)
            mock_path_cls.assert_not_called()

    def test_handles_empty_volume_list(self) -> None:
        """Containers with an empty Volume list should be silently skipped."""
        container = self._make_container([])
        bundle = QuadletBundle(containers=[container])

        from subcommands.up import _ensure_bind_mount_dirs

        with patch("subcommands.up.Path") as mock_path_cls:
            _ensure_bind_mount_dirs(bundle)
            mock_path_cls.assert_not_called()

    @patch("subcommands.up.Path")
    def test_creates_nested_directories(self, mock_path_cls: MagicMock) -> None:
        """Deeply nested bind mount paths are created with parents=True."""
        mock_path = MagicMock()
        mock_path.is_absolute.return_value = True
        mock_path.exists.return_value = False
        mock_path.suffix = ""
        mock_path_cls.return_value = mock_path

        container = self._make_container(["/deep/nested/path/data:/app/data"])
        bundle = QuadletBundle(containers=[container])

        from subcommands.up import _ensure_bind_mount_dirs

        _ensure_bind_mount_dirs(bundle)

        mock_path.mkdir.assert_called_once_with(parents=True, exist_ok=True)

    @patch("subcommands.up.Path")
    def test_mixed_volumes(self, mock_path_cls: MagicMock) -> None:
        """Bind mounts are created; named volumes are skipped."""
        bind_mock = MagicMock()
        bind_mock.is_absolute.return_value = True
        bind_mock.exists.return_value = False
        bind_mock.suffix = ""

        named_mock = MagicMock()
        named_mock.is_absolute.return_value = False

        mock_path_cls.side_effect = [bind_mock, named_mock]

        container = self._make_container(
            ["/tmp/host_data:/app/data", "named_vol:/app/vol"]
        )
        bundle = QuadletBundle(containers=[container])

        from subcommands.up import _ensure_bind_mount_dirs

        _ensure_bind_mount_dirs(bundle)

        bind_mock.mkdir.assert_called_once_with(parents=True, exist_ok=True)
        named_mock.mkdir.assert_not_called()

    @patch("subcommands.up.Path")
    def test_multiple_containers(self, mock_path_cls: MagicMock) -> None:
        """All containers in the bundle are processed."""
        mock_a = MagicMock()
        mock_a.is_absolute.return_value = True
        mock_a.exists.return_value = False
        mock_a.suffix = ""

        mock_b = MagicMock()
        mock_b.is_absolute.return_value = True
        mock_b.exists.return_value = False
        mock_b.suffix = ""

        mock_path_cls.side_effect = [mock_a, mock_b]

        bundle = QuadletBundle(
            containers=[
                self._make_container(["/data/a:/a"]),
                self._make_container(["/data/b:/b"]),
            ]
        )

        from subcommands.up import _ensure_bind_mount_dirs

        _ensure_bind_mount_dirs(bundle)

        mock_a.mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_b.mkdir.assert_called_once_with(parents=True, exist_ok=True)
