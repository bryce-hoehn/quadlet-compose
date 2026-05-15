"""Tests for utils.interpolation — variable interpolation in compose files."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from utils.compose import ComposeError, parse_compose
from utils.interpolation import (
    InterpolationError,
    interpolating_yaml_load,
)


# ---------------------------------------------------------------------------
# interpolating_yaml_load — $VAR and ${VAR} resolution
# ---------------------------------------------------------------------------

class TestInterpolatingYamlLoad:
    """Tests for interpolating_yaml_load()."""

    def test_plain_var_from_os_environ(self, tmp_path: Path) -> None:
        compose = tmp_path / 'compose.yaml'
        compose.write_text('services:\n  web:\n    image: $MY_IMAGE\n')
        with patch.dict(os.environ, {'MY_IMAGE': 'nginx:latest'}):
            data = interpolating_yaml_load(compose)
        assert data['services']['web']['image'] == 'nginx:latest'

    def test_braced_var(self, tmp_path: Path) -> None:
        compose = tmp_path / 'compose.yaml'
        compose.write_text('services:\n  web:\n    image: ${MY_IMAGE}\n')
        with patch.dict(os.environ, {'MY_IMAGE': 'nginx:latest'}):
            data = interpolating_yaml_load(compose)
        assert data['services']['web']['image'] == 'nginx:latest'

    def test_double_quoted_interpolated(self, tmp_path: Path) -> None:
        compose = tmp_path / 'compose.yaml'
        compose.write_text('services:\n  web:\n    image: "${MY_IMAGE}"\n')
        with patch.dict(os.environ, {'MY_IMAGE': 'nginx:latest'}):
            data = interpolating_yaml_load(compose)
        assert data['services']['web']['image'] == 'nginx:latest'

    def test_undefined_var_left_as_literal(self, tmp_path: Path) -> None:
        compose = tmp_path / 'compose.yaml'
        compose.write_text('services:\n  web:\n    image: $UNDEFINED_VAR_XYZ\n')
        os.environ.pop('UNDEFINED_VAR_XYZ', None)
        data = interpolating_yaml_load(compose)
        # os.path.expandvars leaves $UNDEFINED as-is when not set
        assert data['services']['web']['image'] == '$UNDEFINED_VAR_XYZ'

    def test_env_override(self, tmp_path: Path) -> None:
        compose = tmp_path / 'compose.yaml'
        compose.write_text('services:\n  web:\n    image: ${MY_IMAGE}\n')
        with patch.dict(os.environ, {'MY_IMAGE': 'nginx:latest'}):
            data = interpolating_yaml_load(
                compose,
                env_override={'MY_IMAGE': 'custom:override'},
            )
        assert data['services']['web']['image'] == 'custom:override'

    def test_dotenv_file_loaded(self, tmp_path: Path) -> None:
        compose = tmp_path / 'compose.yaml'
        compose.write_text('services:\n  web:\n    image: ${MY_IMAGE}\n')
        (tmp_path / '.env').write_text('MY_IMAGE=redis:alpine\n')
        os.environ.pop('MY_IMAGE', None)
        data = interpolating_yaml_load(compose)
        assert data['services']['web']['image'] == 'redis:alpine'

    def test_dotenv_overrides_os_environ(self, tmp_path: Path) -> None:
        """The .env file takes top priority over os.environ."""
        compose = tmp_path / 'compose.yaml'
        compose.write_text('services:\n  web:\n    image: ${MY_IMAGE}\n')
        (tmp_path / '.env').write_text('MY_IMAGE=from_dotenv\n')
        with patch.dict(os.environ, {'MY_IMAGE': 'from_environ'}):
            data = interpolating_yaml_load(compose)
        assert data['services']['web']['image'] == 'from_dotenv'

    def test_dotenv_overrides_env_override(self, tmp_path: Path) -> None:
        """The .env file takes top priority over CLI --env."""
        compose = tmp_path / 'compose.yaml'
        compose.write_text('services:\n  web:\n    image: ${MY_IMAGE}\n')
        (tmp_path / '.env').write_text('MY_IMAGE=from_dotenv\n')
        data = interpolating_yaml_load(
            compose,
            env_override={'MY_IMAGE': 'from_cli'},
        )
        assert data['services']['web']['image'] == 'from_dotenv'

    def test_multiple_vars_in_one_value(self, tmp_path: Path) -> None:
        compose = tmp_path / 'compose.yaml'
        compose.write_text(
            'services:\n  web:\n    image: "${REPO}/${NAME}:${TAG}"\n'
        )
        with patch.dict(
            os.environ,
            {'REPO': 'myrepo', 'NAME': 'myapp', 'TAG': 'v1'},
        ):
            data = interpolating_yaml_load(compose)
        assert data['services']['web']['image'] == 'myrepo/myapp:v1'

    def test_empty_compose_raises(self, tmp_path: Path) -> None:
        compose = tmp_path / 'compose.yaml'
        compose.write_text('')
        with pytest.raises(ComposeError, match='empty'):
            interpolating_yaml_load(compose)


# ---------------------------------------------------------------------------
# parse_compose integration
# ---------------------------------------------------------------------------

class TestParseComposeInterpolation:
    """Tests that parse_compose() uses interpolation by default."""

    def test_interpolation_enabled_by_default(self, tmp_path: Path) -> None:
        compose = tmp_path / 'compose.yaml'
        compose.write_text(
            'name: test\nservices:\n  web:\n    image: ${TEST_IMG}\n'
        )
        with patch.dict(os.environ, {'TEST_IMG': 'nginx:latest'}):
            data = parse_compose(compose)
        assert data['services']['web']['image'] == 'nginx:latest'

    def test_no_interpolate_skips_resolution(self, tmp_path: Path) -> None:
        compose = tmp_path / 'compose.yaml'
        compose.write_text(
            'name: test\nservices:\n  web:\n    image: ${TEST_IMG}\n'
        )
        with patch.dict(os.environ, {'TEST_IMG': 'nginx:latest'}):
            data = parse_compose(compose, no_interpolate=True)
        assert data['services']['web']['image'] == '${TEST_IMG}'
