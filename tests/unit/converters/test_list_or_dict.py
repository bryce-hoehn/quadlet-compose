"""Tests for utils/converters/_list_or_dict.py."""

from utils.converters._list_or_dict import (
    convert_list_or_dict_to_build_env,
    convert_list_or_dict_to_build_labels,
    convert_list_or_dict_to_env,
    convert_list_or_dict_to_labels,
    convert_list_or_dict_to_sysctls,
)


class TestConvertListOrDictToEnv:
    """Tests for convert_list_or_dict_to_env()."""

    def test_none_returns_empty(self) -> None:
        assert convert_list_or_dict_to_env(None) == {}

    def test_dict(self) -> None:
        result = convert_list_or_dict_to_env({"FOO": "bar", "BAZ": "qux"})
        assert result == {"Environment": ["FOO=bar", "BAZ=qux"]}

    def test_dict_skips_none_values(self) -> None:
        result = convert_list_or_dict_to_env({"FOO": "bar", "EMPTY": None})
        assert result == {"Environment": ["FOO=bar"]}

    def test_list(self) -> None:
        result = convert_list_or_dict_to_env(["FOO=bar", "BAZ=qux"])
        assert result == {"Environment": ["FOO=bar", "BAZ=qux"]}

    def test_empty_dict(self) -> None:
        assert convert_list_or_dict_to_env({}) == {"Environment": []}

    def test_empty_list(self) -> None:
        assert convert_list_or_dict_to_env([]) == {"Environment": []}

    def test_unknown_type_returns_empty(self) -> None:
        assert convert_list_or_dict_to_env(42) == {}


class TestConvertListOrDictToLabels:
    """Tests for convert_list_or_dict_to_labels()."""

    def test_none_returns_empty(self) -> None:
        assert convert_list_or_dict_to_labels(None) == {}

    def test_dict(self) -> None:
        result = convert_list_or_dict_to_labels({"app": "web", "env": "prod"})
        assert result == {"Label": ["app=web", "env=prod"]}

    def test_list(self) -> None:
        result = convert_list_or_dict_to_labels(["app=web", "env=prod"])
        assert result == {"Label": ["app=web", "env=prod"]}

    def test_unknown_type_returns_empty(self) -> None:
        assert convert_list_or_dict_to_labels("string") == {}


class TestConvertListOrDictToSysctls:
    """Tests for convert_list_or_dict_to_sysctls()."""

    def test_none_returns_empty(self) -> None:
        assert convert_list_or_dict_to_sysctls(None) == {}

    def test_dict(self) -> None:
        result = convert_list_or_dict_to_sysctls({"net.core.somaxconn": "1024"})
        assert result == {"Sysctl": ["net.core.somaxconn=1024"]}

    def test_list(self) -> None:
        result = convert_list_or_dict_to_sysctls(["net.core.somaxconn=1024"])
        assert result == {"Sysctl": ["net.core.somaxconn=1024"]}


class TestConvertListOrDictToBuildEnv:
    """Tests for convert_list_or_dict_to_build_env() — alias for env."""

    def test_delegates_to_env(self) -> None:
        result = convert_list_or_dict_to_build_env({"BUILD_ARG": "value"})
        assert result == {"Environment": ["BUILD_ARG=value"]}


class TestConvertListOrDictToBuildLabels:
    """Tests for convert_list_or_dict_to_build_labels() — alias for labels."""

    def test_delegates_to_labels(self) -> None:
        result = convert_list_or_dict_to_build_labels({"version": "1.0"})
        assert result == {"Label": ["version=1.0"]}
