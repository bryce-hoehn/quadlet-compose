"""Tests for utils.compose — resolve_compose_path, parse_compose, ComposeError."""

from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from utils.compose import (
    COMPOSE_FILE_NAMES,
    ComposeError,
    parse_compose,
    resolve_compose_path,
)


class TestComposeError:
    """Tests for the ComposeError exception class."""

    def test_is_exception(self):
        assert issubclass(ComposeError, Exception)

    def test_message(self):
        err = ComposeError("test error")
        assert str(err) == "test error"

    def test_can_be_raised_and_caught(self):
        with pytest.raises(ComposeError, match="boom"):
            raise ComposeError("boom")


class TestComposeFileNames:
    """Tests for the COMPOSE_FILE_NAMES constant."""

    def test_is_list(self):
        assert isinstance(COMPOSE_FILE_NAMES, list)

    def test_contains_standard_names(self):
        assert "compose.yaml" in COMPOSE_FILE_NAMES
        assert "compose.yml" in COMPOSE_FILE_NAMES
        assert "docker-compose.yaml" in COMPOSE_FILE_NAMES
        assert "docker-compose.yml" in COMPOSE_FILE_NAMES

    def test_search_order(self):
        """compose.yaml should be searched first."""
        assert COMPOSE_FILE_NAMES[0] == "compose.yaml"

    def test_all_end_in_yaml_or_yml(self):
        for name in COMPOSE_FILE_NAMES:
            assert name.endswith(".yaml") or name.endswith(".yml")


class TestResolveComposePath:
    """Tests for resolve_compose_path()."""

    def test_explicit_file_exists(self, tmp_path):
        compose_file = tmp_path / "my-compose.yaml"
        compose_file.write_text("services: {}")
        result = resolve_compose_path(str(compose_file))
        assert result == compose_file

    def test_explicit_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError, match="Compose file not found"):
            resolve_compose_path(str(tmp_path / "nonexistent.yaml"))

    def test_none_searches_cwd_found(self, tmp_path):
        """When compose_file is None, searches CWD for standard filenames."""
        compose_file = tmp_path / "compose.yaml"
        compose_file.write_text("services: {}")
        with patch("utils.compose.Path.cwd", return_value=tmp_path):
            result = resolve_compose_path(None)
        assert result == compose_file

    def test_none_searches_cwd_yml(self, tmp_path):
        """Finds compose.yml when compose.yaml doesn't exist."""
        compose_file = tmp_path / "compose.yml"
        compose_file.write_text("services: {}")
        with patch("utils.compose.Path.cwd", return_value=tmp_path):
            result = resolve_compose_path(None)
        assert result == compose_file

    def test_none_searches_cwd_docker_compose(self, tmp_path):
        """Finds docker-compose.yaml when no compose.yaml/yml exists."""
        compose_file = tmp_path / "docker-compose.yaml"
        compose_file.write_text("services: {}")
        with patch("utils.compose.Path.cwd", return_value=tmp_path):
            result = resolve_compose_path(None)
        assert result == compose_file

    def test_none_searches_first_match_wins(self, tmp_path):
        """When multiple compose files exist, first in search order wins."""
        (tmp_path / "compose.yaml").write_text("services: {}")
        (tmp_path / "docker-compose.yaml").write_text("services: {}")
        with patch("utils.compose.Path.cwd", return_value=tmp_path):
            result = resolve_compose_path(None)
        assert result.name == "compose.yaml"

    def test_none_not_found(self, tmp_path):
        """Raises FileNotFoundError when no compose file in CWD."""
        with patch("utils.compose.Path.cwd", return_value=tmp_path):
            with pytest.raises(FileNotFoundError, match="No compose file found"):
                resolve_compose_path(None)

    def test_explicit_path_takes_precedence_over_search(self, tmp_path):
        """Explicit path is used even if CWD has compose files."""
        explicit = tmp_path / "custom-compose.yaml"
        explicit.write_text("services: {}")
        (tmp_path / "compose.yaml").write_text("services: {}")
        result = resolve_compose_path(str(explicit))
        assert result == explicit


class TestParseCompose:
    """Tests for parse_compose()."""

    def test_valid_minimal(self, tmp_path):
        compose_file = tmp_path / "compose.yaml"
        compose_file.write_text("services:\n" "  web:\n" "    image: nginx:latest\n")
        data = parse_compose(compose_file)
        assert "services" in data
        assert "web" in data["services"]
        assert data["services"]["web"]["image"] == "nginx:latest"

    def test_empty_file_raises(self, tmp_path):
        compose_file = tmp_path / "compose.yaml"
        compose_file.write_text("")
        with pytest.raises(ComposeError, match="Compose file is empty"):
            parse_compose(compose_file)

    def test_returns_dict(self, tmp_path):
        compose_file = tmp_path / "compose.yaml"
        compose_file.write_text("services: {}\n")
        data = parse_compose(compose_file)
        assert isinstance(data, dict)

    def test_valid_with_networks(self, tmp_path):
        compose_file = tmp_path / "compose.yaml"
        compose_file.write_text(
            "services:\n"
            "  web:\n"
            "    image: nginx\n"
            "networks:\n"
            "  frontend:\n"
            "    driver: bridge\n"
        )
        data = parse_compose(compose_file)
        assert "networks" in data
        assert "frontend" in data["networks"]

    def test_valid_with_volumes(self, tmp_path):
        compose_file = tmp_path / "compose.yaml"
        compose_file.write_text(
            "services:\n"
            "  db:\n"
            "    image: postgres\n"
            "volumes:\n"
            "  data:\n"
            "    driver: local\n"
        )
        data = parse_compose(compose_file)
        assert "volumes" in data
        assert "data" in data["volumes"]

    def test_valid_with_build(self, tmp_path):
        compose_file = tmp_path / "compose.yaml"
        compose_file.write_text(
            "services:\n"
            "  app:\n"
            "    build:\n"
            "      context: .\n"
            "      dockerfile: Dockerfile\n"
        )
        data = parse_compose(compose_file)
        assert data["services"]["app"]["build"]["context"] == "."

    def test_invalid_yaml_raises(self, tmp_path):
        """Invalid YAML content should raise an error from yaml or pydantic."""
        compose_file = tmp_path / "compose.yaml"
        compose_file.write_text("{{{{invalid yaml")
        with pytest.raises(Exception):
            parse_compose(compose_file)
