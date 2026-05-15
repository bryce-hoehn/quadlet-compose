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
    _extract_env_file_paths,
    _load_env_file_values,
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


# ---------------------------------------------------------------------------
# _extract_env_file_paths — unit tests
# ---------------------------------------------------------------------------

class TestExtractEnvFilePaths:
    """Tests for _extract_env_file_paths()."""

    def test_string_env_file(self, tmp_path: Path) -> None:
        compose = tmp_path / 'compose.yaml'
        data = {'services': {'web': {'env_file': '.env.web'}}}
        paths = _extract_env_file_paths(data, compose)
        assert paths == [tmp_path / '.env.web']

    def test_list_of_strings(self, tmp_path: Path) -> None:
        compose = tmp_path / 'compose.yaml'
        data = {'services': {'web': {'env_file': ['.env.web', '.env.db']}}}
        paths = _extract_env_file_paths(data, compose)
        assert paths == [tmp_path / '.env.web', tmp_path / '.env.db']

    def test_list_of_dicts(self, tmp_path: Path) -> None:
        compose = tmp_path / 'compose.yaml'
        data = {
            'services': {
                'web': {'env_file': [{'path': '.env.web', 'required': True}]},
            },
        }
        paths = _extract_env_file_paths(data, compose)
        assert paths == [tmp_path / '.env.web']

    def test_mixed_list(self, tmp_path: Path) -> None:
        compose = tmp_path / 'compose.yaml'
        data = {
            'services': {
                'web': {
                    'env_file': ['.env.common', {'path': '.env.web'}],
                },
            },
        }
        paths = _extract_env_file_paths(data, compose)
        assert paths == [tmp_path / '.env.common', tmp_path / '.env.web']

    def test_no_env_file(self, tmp_path: Path) -> None:
        compose = tmp_path / 'compose.yaml'
        data = {'services': {'web': {'image': 'nginx'}}}
        paths = _extract_env_file_paths(data, compose)
        assert paths == []

    def test_no_services(self, tmp_path: Path) -> None:
        compose = tmp_path / 'compose.yaml'
        data = {}
        paths = _extract_env_file_paths(data, compose)
        assert paths == []

    def test_multiple_services(self, tmp_path: Path) -> None:
        compose = tmp_path / 'compose.yaml'
        data = {
            'services': {
                'web': {'env_file': '.env.web'},
                'db': {'env_file': ['.env.db']},
            },
        }
        paths = _extract_env_file_paths(data, compose)
        assert paths == [tmp_path / '.env.web', tmp_path / '.env.db']

    def test_relative_path_resolved(self, tmp_path: Path) -> None:
        compose = tmp_path / 'compose.yaml'
        data = {'services': {'web': {'env_file': '../shared.env'}}}
        paths = _extract_env_file_paths(data, compose)
        assert paths == [compose.parent / '../shared.env']
        # Verify the path resolves correctly for file access
        assert paths[0].resolve() == (tmp_path.parent / 'shared.env').resolve()

    def test_none_service_config(self, tmp_path: Path) -> None:
        compose = tmp_path / 'compose.yaml'
        data = {'services': {'web': None}}
        paths = _extract_env_file_paths(data, compose)
        assert paths == []


# ---------------------------------------------------------------------------
# _load_env_file_values — unit tests
# ---------------------------------------------------------------------------

class TestLoadEnvFileValues:
    """Tests for _load_env_file_values()."""

    def test_loads_from_env_file(self, tmp_path: Path) -> None:
        compose = tmp_path / 'compose.yaml'
        (tmp_path / 'web.env').write_text('DB_HOST=db\nDB_PORT=5432\n')
        data = {'services': {'web': {'env_file': 'web.env'}}}
        values = _load_env_file_values(data, compose)
        assert values == {'DB_HOST': 'db', 'DB_PORT': '5432'}

    def test_missing_file_skipped(self, tmp_path: Path) -> None:
        compose = tmp_path / 'compose.yaml'
        data = {'services': {'web': {'env_file': 'nonexistent.env'}}}
        values = _load_env_file_values(data, compose)
        assert values == {}

    def test_multiple_files_merged(self, tmp_path: Path) -> None:
        compose = tmp_path / 'compose.yaml'
        (tmp_path / 'a.env').write_text('A=1\nSHARED=from_a\n')
        (tmp_path / 'b.env').write_text('B=2\nSHARED=from_b\n')
        data = {'services': {'web': {'env_file': ['a.env', 'b.env']}}}
        values = _load_env_file_values(data, compose)
        assert values == {'A': '1', 'B': '2', 'SHARED': 'from_b'}

    def test_multiple_services(self, tmp_path: Path) -> None:
        compose = tmp_path / 'compose.yaml'
        (tmp_path / 'web.env').write_text('WEB_VAR=webval\n')
        (tmp_path / 'db.env').write_text('DB_VAR=dbval\n')
        data = {
            'services': {
                'web': {'env_file': 'web.env'},
                'db': {'env_file': 'db.env'},
            },
        }
        values = _load_env_file_values(data, compose)
        assert values == {'WEB_VAR': 'webval', 'DB_VAR': 'dbval'}


# ---------------------------------------------------------------------------
# env_file interpolation — integration tests
# ---------------------------------------------------------------------------

class TestEnvFileInterpolation:
    """Integration tests for env_file values being available for interpolation."""

    def test_env_file_var_interpolated(self, tmp_path: Path) -> None:
        """Variables from env_file should be available for interpolation."""
        compose = tmp_path / 'compose.yaml'
        (tmp_path / 'app.env').write_text('DB_HOST=mydb\n')
        compose.write_text(
            'services:\n  web:\n    env_file: app.env\n    image: ${DB_HOST}\n'
        )
        os.environ.pop('DB_HOST', None)
        data = interpolating_yaml_load(compose)
        assert data['services']['web']['image'] == 'mydb'

    def test_os_environ_overrides_env_file(self, tmp_path: Path) -> None:
        """OS env vars should take precedence over env_file values."""
        compose = tmp_path / 'compose.yaml'
        (tmp_path / 'app.env').write_text('DB_HOST=from_envfile\n')
        compose.write_text(
            'services:\n  web:\n    env_file: app.env\n    image: ${DB_HOST}\n'
        )
        with patch.dict(os.environ, {'DB_HOST': 'from_os'}):
            data = interpolating_yaml_load(compose)
        assert data['services']['web']['image'] == 'from_os'

    def test_dotenv_overrides_env_file(self, tmp_path: Path) -> None:
        """The .env file should take precedence over env_file values."""
        compose = tmp_path / 'compose.yaml'
        (tmp_path / 'app.env').write_text('DB_HOST=from_envfile\n')
        (tmp_path / '.env').write_text('DB_HOST=from_dotenv\n')
        compose.write_text(
            'services:\n  web:\n    env_file: app.env\n    image: ${DB_HOST}\n'
        )
        os.environ.pop('DB_HOST', None)
        data = interpolating_yaml_load(compose)
        assert data['services']['web']['image'] == 'from_dotenv'

    def test_cli_overrides_env_file(self, tmp_path: Path) -> None:
        """CLI --env should take precedence over env_file values."""
        compose = tmp_path / 'compose.yaml'
        (tmp_path / 'app.env').write_text('DB_HOST=from_envfile\n')
        compose.write_text(
            'services:\n  web:\n    env_file: app.env\n    image: ${DB_HOST}\n'
        )
        data = interpolating_yaml_load(
            compose,
            env_override={'DB_HOST': 'from_cli'},
        )
        assert data['services']['web']['image'] == 'from_cli'

    def test_missing_env_file_handled_gracefully(self, tmp_path: Path) -> None:
        """A missing env_file should not cause an error."""
        compose = tmp_path / 'compose.yaml'
        compose.write_text(
            'services:\n  web:\n    env_file: nonexistent.env\n'
            '    image: ${MY_IMG:-default}\n'
        )
        os.environ.pop('MY_IMG', None)
        data = interpolating_yaml_load(compose)
        assert data['services']['web']['image'] == 'default'

    def test_env_file_as_list(self, tmp_path: Path) -> None:
        """env_file as a list of paths should work."""
        compose = tmp_path / 'compose.yaml'
        (tmp_path / 'first.env').write_text('HOST=first\n')
        (tmp_path / 'second.env').write_text('PORT=8080\n')
        compose.write_text(
            'services:\n  web:\n    env_file:\n      - first.env\n'
            '      - second.env\n    image: "${HOST}:${PORT}"\n'
        )
        os.environ.pop('HOST', None)
        os.environ.pop('PORT', None)
        data = interpolating_yaml_load(compose)
        assert data['services']['web']['image'] == 'first:8080'

    def test_env_file_from_other_service(self, tmp_path: Path) -> None:
        """env_file from one service should be available for all interpolation."""
        compose = tmp_path / 'compose.yaml'
        (tmp_path / 'db.env').write_text('DB_HOST=mydb\n')
        compose.write_text(
            'services:\n  db:\n    env_file: db.env\n    image: postgres\n'
            '  web:\n    image: ${DB_HOST}\n'
        )
        os.environ.pop('DB_HOST', None)
        data = interpolating_yaml_load(compose)
        assert data['services']['web']['image'] == 'mydb'
