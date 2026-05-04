"""Tests for hacks.interpolate._load_dotenv — .env file loading."""

import pytest
from pathlib import Path

from hacks.interpolate import _load_dotenv


class TestLoadDotenv:
    """Test .env file parsing next to compose files."""

    def test_loads_key_value_pairs(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("DB_HOST=localhost\nPORT=5432\n")
        result = _load_dotenv(tmp_path / "compose.yaml")
        assert result == {"DB_HOST": "localhost", "PORT": "5432"}

    def test_skips_comments(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("# This is a comment\nKEY=value\n# Another comment\n")
        result = _load_dotenv(tmp_path / "compose.yaml")
        assert result == {"KEY": "value"}

    def test_skips_blank_lines(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("\n\nKEY=value\n\n")
        result = _load_dotenv(tmp_path / "compose.yaml")
        assert result == {"KEY": "value"}

    def test_strips_whitespace(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("  KEY  =  value  \n")
        result = _load_dotenv(tmp_path / "compose.yaml")
        assert result == {"KEY": "value"}

    def test_strips_quotes(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text('KEY="quoted"\nSINGLE=\'single\'\n')
        result = _load_dotenv(tmp_path / "compose.yaml")
        assert result == {"KEY": "quoted", "SINGLE": "single"}

    def test_returns_empty_when_no_env_file(self, tmp_path):
        result = _load_dotenv(tmp_path / "compose.yaml")
        assert result == {}

    def test_skips_lines_without_equals(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("JUST_A_WORD\nKEY=value\n")
        result = _load_dotenv(tmp_path / "compose.yaml")
        assert result == {"KEY": "value"}

    def test_value_with_equals_sign(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("CONNECTION_STRING=host=db port=5432\n")
        result = _load_dotenv(tmp_path / "compose.yaml")
        assert result == {"CONNECTION_STRING": "host=db port=5432"}

    def test_empty_value(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("EMPTY=\n")
        result = _load_dotenv(tmp_path / "compose.yaml")
        assert result == {"EMPTY": ""}
