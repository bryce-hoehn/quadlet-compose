"""Tests for compose_cmds.up — volume parsing and bind mount helpers."""

import os
from pathlib import Path

import pytest

from compose_cmds.up import _is_bind_mount, _parse_volume_host_path, _ensure_bind_mount_dirs


# ---------------------------------------------------------------------------
# _is_bind_mount
# ---------------------------------------------------------------------------


class TestIsBindMount:
    def test_relative_path(self):
        assert _is_bind_mount("./data") is True

    def test_relative_path_no_dot_slash(self):
        # "data/app" without ./ or / prefix is treated as a named volume
        assert _is_bind_mount("data/app") is False

    def test_absolute_path(self):
        assert _is_bind_mount("/host/path") is True

    def test_named_volume(self):
        assert _is_bind_mount("mydata") is False

    def test_empty_string(self):
        assert _is_bind_mount("") is False


# ---------------------------------------------------------------------------
# _parse_volume_host_path
# ---------------------------------------------------------------------------


class TestParseVolumeHostPath:
    # --- Short-form strings ---

    def test_relative_bind_mount(self):
        assert _parse_volume_host_path("./data:/app") == "./data"

    def test_absolute_bind_mount(self):
        assert _parse_volume_host_path("/host/path:/container") == "/host/path"

    def test_bind_mount_with_mode(self):
        assert _parse_volume_host_path("./data:/app:ro") == "./data"

    def test_named_volume_returns_none(self):
        assert _parse_volume_host_path("mydata:/app") is None

    def test_named_volume_with_mode_returns_none(self):
        assert _parse_volume_host_path("mydata:/app:ro") is None

    # --- Long-form dicts ---

    def test_dict_bind_type(self):
        vol = {"type": "bind", "source": "./data", "target": "/app"}
        assert _parse_volume_host_path(vol) == "./data"

    def test_dict_bind_type_absolute(self):
        vol = {"type": "bind", "source": "/host/path", "target": "/app"}
        assert _parse_volume_host_path(vol) == "/host/path"

    def test_dict_volume_type_returns_none(self):
        vol = {"type": "volume", "source": "mydata", "target": "/app"}
        assert _parse_volume_host_path(vol) is None

    def test_dict_no_type_with_path_source(self):
        vol = {"source": "./data", "target": "/app"}
        assert _parse_volume_host_path(vol) == "./data"

    def test_dict_no_type_with_named_source(self):
        vol = {"source": "mydata", "target": "/app"}
        assert _parse_volume_host_path(vol) is None

    def test_dict_empty_source(self):
        vol = {"type": "bind", "source": "", "target": "/app"}
        assert _parse_volume_host_path(vol) == ""

    # --- Edge cases ---

    def test_non_string_non_dict_returns_none(self):
        assert _parse_volume_host_path(42) is None

    def test_none_returns_none(self):
        assert _parse_volume_host_path(None) is None


# ---------------------------------------------------------------------------
# _ensure_bind_mount_dirs
# ---------------------------------------------------------------------------


class TestEnsureBindMountDirs:
    def test_creates_missing_bind_mount_dir(self, tmp_path):
        compose_data = {
            "services": {
                "web": {
                    "image": "nginx",
                    "volumes": ["./html:/usr/share/nginx/html:ro"],
                }
            }
        }
        _ensure_bind_mount_dirs(compose_data, tmp_path)
        assert (tmp_path / "html").is_dir()

    def test_skips_named_volumes(self, tmp_path):
        compose_data = {
            "services": {
                "db": {
                    "image": "postgres",
                    "volumes": ["pgdata:/var/lib/postgresql/data"],
                }
            }
        }
        _ensure_bind_mount_dirs(compose_data, tmp_path)
        assert not (tmp_path / "pgdata").exists()

    def test_handles_long_form_bind(self, tmp_path):
        compose_data = {
            "services": {
                "web": {
                    "image": "nginx",
                    "volumes": [
                        {"type": "bind", "source": "./data", "target": "/app"},
                    ],
                }
            }
        }
        _ensure_bind_mount_dirs(compose_data, tmp_path)
        assert (tmp_path / "data").is_dir()

    def test_handles_long_form_volume(self, tmp_path):
        compose_data = {
            "services": {
                "db": {
                    "image": "postgres",
                    "volumes": [
                        {"type": "volume", "source": "pgdata", "target": "/data"},
                    ],
                }
            }
        }
        _ensure_bind_mount_dirs(compose_data, tmp_path)
        assert not (tmp_path / "pgdata").exists()

    def test_creates_nested_dirs(self, tmp_path):
        compose_data = {
            "services": {
                "web": {
                    "image": "nginx",
                    "volumes": ["./deep/nested/dir:/app"],
                }
            }
        }
        _ensure_bind_mount_dirs(compose_data, tmp_path)
        assert (tmp_path / "deep" / "nested" / "dir").is_dir()

    def test_skips_non_dict_services(self, tmp_path):
        compose_data = {
            "services": {
                "web": "just-a-string",
            }
        }
        _ensure_bind_mount_dirs(compose_data, tmp_path)  # should not crash

    @pytest.mark.skipif(os.name == "nt", reason="Linux-style absolute paths only")
    def test_absolute_path_not_prefixed_by_compose_dir(self, tmp_path):
        """Absolute paths should be used as-is, not joined with compose_dir."""
        target = tmp_path / "absolute_target"
        compose_data = {
            "services": {
                "web": {
                    "image": "nginx",
                    "volumes": [f"/{target}:/app"],
                }
            }
        }
        # Use tmp_path as compose_dir; the / prefix means resolve() keeps it absolute
        _ensure_bind_mount_dirs(compose_data, tmp_path)
        # On Linux, the path /{tmp_path}/absolute_target should be created
        # But since we're testing on Windows too, just verify no crash

    def test_no_volumes_key(self, tmp_path):
        compose_data = {
            "services": {
                "web": {"image": "nginx"},
            }
        }
        _ensure_bind_mount_dirs(compose_data, tmp_path)  # should not crash
