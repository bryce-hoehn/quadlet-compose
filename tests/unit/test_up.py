"""Tests for utils/_helpers.py helpers."""

from utils._helpers import extract_hash, quadlet_to_service


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
