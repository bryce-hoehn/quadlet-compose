"""Tests for utils.interpolation — variable interpolation in compose files."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from utils.compose import ComposeError, parse_compose
from utils.interpolation import (
    InvalidInterpolation,
    TemplateWithDefaults,
    UnsetRequiredSubstitution,
    interpolating_yaml_load,
)


# ---------------------------------------------------------------------------
# TemplateWithDefaults — unit tests for the template engine
# ---------------------------------------------------------------------------

class TestTemplateWithDefaults:
    """Tests for the TemplateWithDefaults string.Template subclass."""

    def test_plain_var(self) -> None:
        result = TemplateWithDefaults('$NAME').substitute({'NAME': 'alice'})
        assert result == 'alice'

    def test_braced_var(self) -> None:
        result = TemplateWithDefaults('${NAME}').substitute({'NAME': 'alice'})
        assert result == 'alice'

    def test_undefined_var_returns_empty(self) -> None:
        result = TemplateWithDefaults('$UNDEF').substitute({})
        assert result == ''

    def test_undefined_braced_returns_empty(self) -> None:
        result = TemplateWithDefaults('${UNDEF}').substitute({})
        assert result == ''

    def test_dollar_dollar_escaped(self) -> None:
        result = TemplateWithDefaults('price is $$5').substitute({})
        assert result == 'price is $5'

    def test_dollar_dollar_before_var(self) -> None:
        result = TemplateWithDefaults('$$${NAME}').substitute({'NAME': 'alice'})
        assert result == '$alice'

    # -- Default value modifiers --

    def test_default_if_unset_or_empty(self) -> None:
        """${VAR:-default} → default if unset or empty."""
        assert TemplateWithDefaults('${VAR:-fallback}').substitute({}) == 'fallback'
        assert TemplateWithDefaults('${VAR:-fallback}').substitute({'VAR': ''}) == 'fallback'
        assert TemplateWithDefaults('${VAR:-fallback}').substitute({'VAR': 'set'}) == 'set'

    def test_default_if_unset(self) -> None:
        """${VAR-default} → default if unset (empty is kept)."""
        assert TemplateWithDefaults('${VAR-fallback}').substitute({}) == 'fallback'
        assert TemplateWithDefaults('${VAR-fallback}').substitute({'VAR': ''}) == ''
        assert TemplateWithDefaults('${VAR-fallback}').substitute({'VAR': 'set'}) == 'set'

    # -- Required value modifiers --

    def test_required_if_unset_or_empty(self) -> None:
        """${VAR:?error} → error if unset or empty."""
        with pytest.raises(UnsetRequiredSubstitution):
            TemplateWithDefaults('${VAR:?missing}').substitute({})
        with pytest.raises(UnsetRequiredSubstitution):
            TemplateWithDefaults('${VAR:?missing}').substitute({'VAR': ''})
        assert TemplateWithDefaults('${VAR:?missing}').substitute({'VAR': 'ok'}) == 'ok'

    def test_required_if_unset(self) -> None:
        """${VAR?error} → error if unset (empty is ok)."""
        with pytest.raises(UnsetRequiredSubstitution):
            TemplateWithDefaults('${VAR?missing}').substitute({})
        assert TemplateWithDefaults('${VAR?missing}').substitute({'VAR': ''}) == ''
        assert TemplateWithDefaults('${VAR?missing}').substitute({'VAR': 'ok'}) == 'ok'

    # -- Alternative value modifiers --

    def test_alternative_if_set_and_nonempty(self) -> None:
        """${VAR:+replacement} → replacement if set and non-empty."""
        assert TemplateWithDefaults('${VAR:+yes}').substitute({}) == ''
        assert TemplateWithDefaults('${VAR:+yes}').substitute({'VAR': ''}) == ''
        assert TemplateWithDefaults('${VAR:+yes}').substitute({'VAR': 'set'}) == 'yes'

    def test_alternative_if_set(self) -> None:
        """${VAR+replacement} → replacement if set (even if empty)."""
        assert TemplateWithDefaults('${VAR+yes}').substitute({}) == ''
        assert TemplateWithDefaults('${VAR+yes}').substitute({'VAR': ''}) == 'yes'
        assert TemplateWithDefaults('${VAR+yes}').substitute({'VAR': 'set'}) == 'yes'

    # -- Multiple vars in one string --

    def test_multiple_vars(self) -> None:
        result = TemplateWithDefaults('${A}/${B}:${C}').substitute(
            {'A': 'repo', 'B': 'app', 'C': 'v1'},
        )
        assert result == 'repo/app:v1'

    def test_mixed_syntax(self) -> None:
        result = TemplateWithDefaults('$A-${B:-default}-$$').substitute({'A': 'hello'})
        assert result == 'hello-default-$'


# ---------------------------------------------------------------------------
# interpolating_yaml_load — integration tests
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

    def test_undefined_var_becomes_empty(self, tmp_path: Path) -> None:
        compose = tmp_path / 'compose.yaml'
        compose.write_text('services:\n  web:\n    image: $UNDEFINED_VAR_XYZ\n')
        os.environ.pop('UNDEFINED_VAR_XYZ', None)
        data = interpolating_yaml_load(compose)
        assert data['services']['web']['image'] == ''

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

    def test_cli_overrides_dotenv(self, tmp_path: Path) -> None:
        """CLI --env takes top priority over .env file."""
        compose = tmp_path / 'compose.yaml'
        compose.write_text('services:\n  web:\n    image: ${MY_IMAGE}\n')
        (tmp_path / '.env').write_text('MY_IMAGE=from_dotenv\n')
        data = interpolating_yaml_load(
            compose,
            env_override={'MY_IMAGE': 'from_cli'},
        )
        assert data['services']['web']['image'] == 'from_cli'

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

    def test_dollar_dollar_escaped(self, tmp_path: Path) -> None:
        compose = tmp_path / 'compose.yaml'
        compose.write_text('services:\n  web:\n    image: "my$$image"\n')
        data = interpolating_yaml_load(compose)
        assert data['services']['web']['image'] == 'my$image'

    def test_default_modifier(self, tmp_path: Path) -> None:
        compose = tmp_path / 'compose.yaml'
        compose.write_text(
            'services:\n  web:\n    image: "${MY_IMAGE:-nginx:latest}"\n'
        )
        os.environ.pop('MY_IMAGE', None)
        data = interpolating_yaml_load(compose)
        assert data['services']['web']['image'] == 'nginx:latest'

    def test_required_modifier_raises(self, tmp_path: Path) -> None:
        compose = tmp_path / 'compose.yaml'
        compose.write_text(
            'services:\n  web:\n    image: "${MY_IMAGE:?image required}"\n'
        )
        os.environ.pop('MY_IMAGE', None)
        with pytest.raises(UnsetRequiredSubstitution):
            interpolating_yaml_load(compose)

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
