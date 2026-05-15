"""Tests for utils/converters/build.py."""

from utils.converters.build import (
    convert_build_context,
    convert_build_dockerfile,
    convert_build_labels,
    convert_build_network,
    convert_build_pull,
    convert_build_secrets,
    convert_build_target,
)


class TestConvertBuildContext:
    def test_none(self) -> None:
        assert convert_build_context(None) == {}

    def test_string(self) -> None:
        assert convert_build_context(".") == {"SetWorkingDirectory": "."}

    def test_path(self) -> None:
        assert convert_build_context("/app") == {"SetWorkingDirectory": "/app"}


class TestConvertBuildDockerfile:
    def test_none(self) -> None:
        assert convert_build_dockerfile(None) == {}

    def test_string(self) -> None:
        assert convert_build_dockerfile("Dockerfile.prod") == {
            "File": "Dockerfile.prod"
        }


class TestConvertBuildTarget:
    def test_none(self) -> None:
        assert convert_build_target(None) == {}

    def test_string(self) -> None:
        assert convert_build_target("production") == {"Target": "production"}


class TestConvertBuildPull:
    def test_none(self) -> None:
        assert convert_build_pull(None) == {}

    def test_false(self) -> None:
        assert convert_build_pull(False) == {}

    def test_true(self) -> None:
        assert convert_build_pull(True) == {"Pull": "true"}


class TestConvertBuildNetwork:
    def test_none(self) -> None:
        assert convert_build_network(None) == {}

    def test_string(self) -> None:
        assert convert_build_network("host") == {"Network": "host"}


class TestConvertBuildSecrets:
    def test_none(self) -> None:
        assert convert_build_secrets(None) == {}

    def test_list(self) -> None:
        result = convert_build_secrets(["my_secret", "other_secret"])
        assert result == {"Secret": ["my_secret", "other_secret"]}

    def test_single_string(self) -> None:
        result = convert_build_secrets("my_secret")
        assert result == {"Secret": ["my_secret"]}


class TestConvertBuildLabels:
    def test_none(self) -> None:
        assert convert_build_labels(None) == {}

    def test_dict(self) -> None:
        result = convert_build_labels({"version": "1.0", "app": "web"})
        assert result == {"Label": ["version=1.0", "app=web"]}

    def test_list(self) -> None:
        result = convert_build_labels(["version=1.0", "app=web"])
        assert result == {"Label": ["version=1.0", "app=web"]}

    def test_unknown_type(self) -> None:
        assert convert_build_labels(42) == {}
