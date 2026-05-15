"""Tests for utils/converters/volume.py."""

from utils.converters.volume import (
    convert_volume_labels,
    convert_volume_name,
)


class TestConvertVolumeName:
    def test_none(self) -> None:
        assert convert_volume_name(None) == {}

    def test_string(self) -> None:
        assert convert_volume_name("my-volume") == {"VolumeName": "my-volume"}


class TestConvertVolumeLabels:
    def test_none(self) -> None:
        assert convert_volume_labels(None) == {}

    def test_dict(self) -> None:
        result = convert_volume_labels({"app": "web", "env": "prod"})
        assert result == {"Label": ["app=web", "env=prod"]}

    def test_list(self) -> None:
        result = convert_volume_labels(["app=web"])
        assert result == {"Label": ["app=web"]}

    def test_unknown_type(self) -> None:
        assert convert_volume_labels(42) == {}
