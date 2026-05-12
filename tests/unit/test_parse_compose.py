"""Tests for utils.compose — compose file parsing and transformations."""

import os
from pathlib import Path

import pytest

from hacks import _iter_services
from hacks.normalize import normalize_service_fields
from hacks.expand import expand_single_values
from hacks.strip_extensions import strip_extensions
from utils.compose import (
    parse_compose,
    resolve_compose_path,
    prepare_compose,
    get_image_services,
    get_build_services,
    COMPOSE_FILE_NAMES,
)
from utils.utils import ComposeError

# ---------------------------------------------------------------------------
# parse_compose
# ---------------------------------------------------------------------------


class TestParseCompose:
    """Test parse_compose() against fixture files."""

    def test_returns_project_name(self, compose_path):
        result = parse_compose(compose_path)
        assert result["project"] == "test-compose"

    def test_returns_service_names(self, compose_path):
        result = parse_compose(compose_path)
        assert "web" in result["service_names"]
        assert "db" in result["service_names"]

    def test_returns_services_dict(self, compose_path):
        result = parse_compose(compose_path)
        assert "web" in result["services"]
        assert result["services"]["web"]["image"] == "docker.io/library/nginx:alpine"

    def test_returns_volume_names(self, compose_path):
        result = parse_compose(compose_path)
        # test-compose/compose.yaml has no named volumes
        assert result["volume_names"] == []

    def test_returns_network_names(self, compose_path):
        result = parse_compose(compose_path)
        # test-compose/compose.yaml has no named networks
        assert result["network_names"] == []

    def test_empty_compose_file(self, tmp_path):
        compose_file = tmp_path / "compose.yaml"
        compose_file.write_text("{}\n")
        result = parse_compose(compose_file)
        assert result["project"] == tmp_path.name
        assert result["service_names"] == []
        assert result["services"] == {}

    def test_compose_with_named_volumes(self, tmp_path):
        compose_file = tmp_path / "compose.yaml"
        compose_file.write_text(
            "name: vols-test\nservices:\n  web:\n    image: nginx\nvolumes:\n  data:\n"
        )
        result = parse_compose(compose_file)
        assert result["volume_names"] == ["data"]

    def test_compose_with_named_networks(self, tmp_path):
        compose_file = tmp_path / "compose.yaml"
        compose_file.write_text(
            "name: net-test\nservices:\n  web:\n    image: nginx\nnetworks:\n  frontend:\n"
        )
        result = parse_compose(compose_file)
        assert result["network_names"] == ["frontend"]

    def test_project_name_from_directory(self, tmp_path):
        """When no `name:` field, project name comes from directory name."""
        compose_file = tmp_path / "compose.yaml"
        compose_file.write_text("services:\n  web:\n    image: nginx\n")
        result = parse_compose(compose_file)
        assert result["project"] == tmp_path.name


# ---------------------------------------------------------------------------
# resolve_compose_path
# ---------------------------------------------------------------------------


class TestResolveComposePath:
    """Test compose file path resolution."""

    def test_explicit_file_path(self, compose_path):
        resolved = resolve_compose_path(str(compose_path))
        assert resolved == compose_path
        assert resolved.is_file()

    def test_raises_on_missing_file(self):
        with pytest.raises(ComposeError, match="Compose file not found"):
            resolve_compose_path("/nonexistent/path/compose.yaml")

    def test_raises_when_no_compose_in_cwd(self, monkeypatch, tmp_path):
        monkeypatch.chdir(tmp_path)
        with pytest.raises(ComposeError, match="No compose file found"):
            resolve_compose_path(None)

    def test_finds_compose_yaml_in_cwd(self, monkeypatch, tmp_path):
        compose_file = tmp_path / "compose.yaml"
        compose_file.write_text("services: {}\n")
        monkeypatch.chdir(tmp_path)
        resolved = resolve_compose_path(None)
        assert resolved.name == "compose.yaml"

    def test_search_order_respected(self, monkeypatch, tmp_path):
        """compose.yaml is preferred over docker-compose.yaml."""
        (tmp_path / "docker-compose.yaml").write_text("services: {}\n")
        (tmp_path / "compose.yaml").write_text("services: {}\n")
        monkeypatch.chdir(tmp_path)
        resolved = resolve_compose_path(None)
        assert resolved.name == "compose.yaml"


# ---------------------------------------------------------------------------
# get_image_services / get_build_services
# ---------------------------------------------------------------------------


class TestGetImageServices:
    def test_extracts_image_services(self):
        data = {
            "services": {
                "web": {"image": "nginx:alpine"},
                "db": {"image": "redis:alpine"},
            }
        }
        result = get_image_services(data)
        assert result == {"web": "nginx:alpine", "db": "redis:alpine"}

    def test_skips_build_only_services(self):
        data = {
            "services": {
                "web": {"image": "nginx"},
                "app": {"build": "."},
            }
        }
        result = get_image_services(data)
        assert result == {"web": "nginx"}

    def test_empty_services(self):
        result = get_image_services({"services": {}})
        assert result == {}


class TestGetBuildServices:
    def test_extracts_string_build(self):
        data = {"services": {"app": {"build": "./dir"}}}
        result = get_build_services(data)
        assert result == {"app": {"context": "./dir"}}

    def test_extracts_dict_build(self):
        data = {
            "services": {"app": {"build": {"context": ".", "dockerfile": "Dockerfile"}}}
        }
        result = get_build_services(data)
        assert result == {"app": {"context": ".", "dockerfile": "Dockerfile"}}

    def test_skips_image_only_services(self):
        data = {"services": {"web": {"image": "nginx"}}}
        result = get_build_services(data)
        assert result == {}


# ---------------------------------------------------------------------------
# normalize_service_fields (hacks.normalize)
# ---------------------------------------------------------------------------


class TestNormalizeServiceFields:
    def test_strips_hostname(self):
        data = {"services": {"web": {"image": "nginx", "hostname": "myhost"}}}
        normalize_service_fields(data)
        assert "hostname" not in data["services"]["web"]

    def test_strips_network_mode(self):
        data = {"services": {"web": {"image": "nginx", "network_mode": "host"}}}
        normalize_service_fields(data)
        assert "network_mode" not in data["services"]["web"]

    def test_strips_image_tag_when_digest_present(self):
        data = {"services": {"web": {"image": "foo:v1@sha256:abc123"}}}
        normalize_service_fields(data)
        assert data["services"]["web"]["image"] == "foo@sha256:abc123"

    def test_keeps_image_tag_without_digest(self):
        data = {"services": {"web": {"image": "nginx:alpine"}}}
        normalize_service_fields(data)
        assert data["services"]["web"]["image"] == "nginx:alpine"

    def test_strips_unsupported_depends_on_conditions(self):
        data = {
            "services": {
                "web": {
                    "image": "nginx",
                    "depends_on": {
                        "db": {"condition": "service_healthy"},
                    },
                },
            }
        }
        normalize_service_fields(data)
        # Should reduce to short form since all entries reduced to None
        assert data["services"]["web"]["depends_on"] == ["db"]

    def test_preserves_required_depends_on(self):
        data = {
            "services": {
                "web": {
                    "image": "nginx",
                    "depends_on": {
                        "db": {"condition": "service_started", "required": True},
                    },
                },
            }
        }
        normalize_service_fields(data)
        dep = data["services"]["web"]["depends_on"]
        assert isinstance(dep, dict)
        assert dep["db"]["required"] is True

    def test_strips_configs(self):
        data = {"services": {"web": {"image": "nginx", "configs": ["myconfig"]}}}
        normalize_service_fields(data)
        assert "configs" not in data["services"]["web"]

    def test_strips_non_external_secrets(self):
        data = {"services": {"web": {"image": "nginx", "secrets": ["my_secret"]}}}
        normalize_service_fields(data)
        assert "secrets" not in data["services"]["web"]

    def test_keeps_external_secrets(self):
        data = {
            "services": {
                "web": {
                    "image": "nginx",
                    "secrets": [
                        {"external": True, "source": "my_secret"},
                        "non_external",
                    ],
                }
            }
        }
        normalize_service_fields(data)
        secrets = data["services"]["web"]["secrets"]
        assert len(secrets) == 1
        assert secrets[0]["external"] is True


# ---------------------------------------------------------------------------
# expand_single_values (hacks.expand)
# ---------------------------------------------------------------------------


class TestExpandSingleValues:
    def test_expands_single_port(self):
        data = {"services": {"web": {"image": "nginx", "ports": ["8080"]}}}
        expand_single_values(data)
        assert data["services"]["web"]["ports"] == ["8080:8080"]

    def test_preserves_full_port(self):
        data = {"services": {"web": {"image": "nginx", "ports": ["8080:80"]}}}
        expand_single_values(data)
        assert data["services"]["web"]["ports"] == ["8080:80"]

    def test_expands_single_device(self):
        data = {"services": {"web": {"image": "nginx", "devices": ["/dev/dri"]}}}
        expand_single_values(data)
        assert data["services"]["web"]["devices"] == ["/dev/dri:/dev/dri"]

    def test_expands_path_like_volume(self):
        data = {"services": {"web": {"image": "nginx", "volumes": ["./data"]}}}
        expand_single_values(data)
        assert data["services"]["web"]["volumes"] == ["./data:./data"]

    def test_preserves_named_volume(self):
        data = {"services": {"web": {"image": "nginx", "volumes": ["data"]}}}
        expand_single_values(data)
        assert data["services"]["web"]["volumes"] == ["data"]

    def test_preserves_full_volume_mount(self):
        data = {"services": {"web": {"image": "nginx", "volumes": ["./data:/app"]}}}
        expand_single_values(data)
        assert data["services"]["web"]["volumes"] == ["./data:/app"]


# ---------------------------------------------------------------------------
# strip_extensions (hacks.strip_extensions)
# ---------------------------------------------------------------------------


class TestStripExtensions:
    def test_removes_x_prefix_keys(self):
        data = {"services": {}, "x-custom": {"foo": "bar"}, "x-env": "test"}
        strip_extensions(data)
        assert "x-custom" not in data
        assert "x-env" not in data

    def test_preserves_non_extension_keys(self):
        data = {"services": {}, "volumes": {}, "networks": {}}
        strip_extensions(data)
        assert "services" in data
        assert "volumes" in data
        assert "networks" in data


# ---------------------------------------------------------------------------
# _iter_services
# ---------------------------------------------------------------------------


class TestIterServices:
    def test_yields_dict_services(self):
        data = {"services": {"web": {"image": "nginx"}, "db": {"image": "redis"}}}
        result = list(_iter_services(data))
        assert len(result) == 2
        assert result[0][0] == "web"
        assert result[1][0] == "db"

    def test_skips_non_dict_services(self):
        data = {"services": {"web": {"image": "nginx"}, "bad": "not-a-dict"}}
        result = list(_iter_services(data))
        assert len(result) == 1
        assert result[0][0] == "web"

    def test_returns_empty_for_no_services(self):
        data = {}
        result = list(_iter_services(data))
        assert result == []


# ---------------------------------------------------------------------------
# prepare_compose (integration-level unit test)
# ---------------------------------------------------------------------------


class TestPrepareCompose:
    """Tests for prepare_compose with hacks enabled/disabled."""

    def test_all_hacks_applied_by_default(self, tmp_path, monkeypatch):
        """When QUADLET_COMPOSE_HACKS is unset, all hacks are applied."""
        monkeypatch.delenv("QUADLET_COMPOSE_HACKS", raising=False)
        monkeypatch.setenv("TEST_IMAGE", "nginx:alpine")
        compose_file = tmp_path / "compose.yaml"
        compose_file.write_text(
            "services:\n  web:\n    image: ${TEST_IMAGE}\nx-custom: foo\n"
        )
        result_path = prepare_compose(compose_file)
        try:
            content = result_path.read_text()
            assert f"name: {tmp_path.name}" in content
            assert "nginx:alpine" in content
            assert "x-custom" not in content
        finally:
            result_path.unlink(missing_ok=True)

    def test_false_disables_all_hacks(self, tmp_path, monkeypatch):
        """QUADLET_COMPOSE_HACKS=false disables every hack."""
        monkeypatch.setenv("QUADLET_COMPOSE_HACKS", "false")
        compose_file = tmp_path / "compose.yaml"
        compose_file.write_text(
            "services:\n  web:\n    image: ${TEST_IMAGE}\nx-custom: foo\n"
        )
        result_path = prepare_compose(compose_file)
        try:
            content = result_path.read_text()
            assert "name:" not in content
            assert "${TEST_IMAGE}" in content
            assert "x-custom" in content
        finally:
            result_path.unlink(missing_ok=True)

    def test_interpolates_env_vars_by_default(self, tmp_path, monkeypatch):
        monkeypatch.delenv("QUADLET_COMPOSE_HACKS", raising=False)
        monkeypatch.setenv("TEST_IMAGE", "nginx:alpine")
        compose_file = tmp_path / "compose.yaml"
        compose_file.write_text(
            "name: test\nservices:\n  web:\n    image: ${TEST_IMAGE}\n"
        )
        result_path = prepare_compose(compose_file)
        try:
            content = result_path.read_text()
            assert "nginx:alpine" in content
        finally:
            result_path.unlink(missing_ok=True)

    def test_strips_extensions_by_default(self, tmp_path, monkeypatch):
        """x-* keys are removed by default."""
        monkeypatch.delenv("QUADLET_COMPOSE_HACKS", raising=False)
        compose_file = tmp_path / "compose.yaml"
        compose_file.write_text(
            "name: test\nservices:\n  web:\n    image: nginx\nx-custom: foo\n"
        )
        result_path = prepare_compose(compose_file)
        try:
            content = result_path.read_text()
            assert "x-custom" not in content
        finally:
            result_path.unlink(missing_ok=True)

    def test_uses_dotenv_values_by_default(self, tmp_path, monkeypatch):
        monkeypatch.delenv("QUADLET_COMPOSE_HACKS", raising=False)
        monkeypatch.delenv("MY_IMAGE", raising=False)
        (tmp_path / ".env").write_text("MY_IMAGE=redis:alpine\n")
        compose_file = tmp_path / "compose.yaml"
        compose_file.write_text(
            "name: test\nservices:\n  cache:\n    image: ${MY_IMAGE}\n"
        )
        result_path = prepare_compose(compose_file)
        try:
            content = result_path.read_text()
            assert "redis:alpine" in content
        finally:
            result_path.unlink(missing_ok=True)
