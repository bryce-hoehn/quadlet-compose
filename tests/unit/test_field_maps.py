"""Tests for field map structure and integrity.

Each field map must be a list of 3-tuples ``(compose_attr, quadlet_attr, converter | None)``
where:
- ``compose_attr`` is a non-empty string
- ``quadlet_attr`` is a string (empty string signals 1:N expansion)
- ``converter`` is ``None`` or a callable
"""

from typing import Callable

import pytest

from utils.field_maps import (
    BUILD_FIELD_MAP,
    NETWORK_FIELD_MAP,
    SERVICE_FIELD_MAP,
    VOLUME_FIELD_MAP,
)

# ---------------------------------------------------------------------------
# Shared structural checks
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "name,fmap",
    [
        ("SERVICE_FIELD_MAP", SERVICE_FIELD_MAP),
        ("BUILD_FIELD_MAP", BUILD_FIELD_MAP),
        ("NETWORK_FIELD_MAP", NETWORK_FIELD_MAP),
        ("VOLUME_FIELD_MAP", VOLUME_FIELD_MAP),
    ],
)
class TestFieldMapStructure:
    """Validate that every field map conforms to the expected structure."""

    def test_is_list(self, name: str, fmap: list) -> None:
        assert isinstance(fmap, list), f"{name} should be a list"

    def test_non_empty(self, name: str, fmap: list) -> None:
        assert len(fmap) > 0, f"{name} should not be empty"

    def test_entries_are_tuples(self, name: str, fmap: list) -> None:
        for i, entry in enumerate(fmap):
            assert isinstance(entry, tuple), f"{name}[{i}] should be a tuple"

    def test_entries_have_three_elements(self, name: str, fmap: list) -> None:
        for i, entry in enumerate(fmap):
            assert (
                len(entry) == 3
            ), f"{name}[{i}] should have 3 elements, got {len(entry)}"

    def test_compose_attr_is_string(self, name: str, fmap: list) -> None:
        for i, entry in enumerate(fmap):
            compose_attr = entry[0]
            assert (
                isinstance(compose_attr, str) and compose_attr
            ), f"{name}[{i}].compose_attr should be a non-empty string"

    def test_quadlet_attr_is_string(self, name: str, fmap: list) -> None:
        for i, entry in enumerate(fmap):
            quadlet_attr = entry[1]
            assert isinstance(
                quadlet_attr, str
            ), f"{name}[{i}].quadlet_attr should be a string (may be empty for 1:N)"

    def test_converter_is_callable_or_none(self, name: str, fmap: list) -> None:
        for i, entry in enumerate(fmap):
            converter = entry[2]
            assert converter is None or isinstance(
                converter, Callable
            ), f"{name}[{i}].converter should be None or callable"

    def test_no_duplicate_compose_attrs(self, name: str, fmap: list) -> None:
        compose_attrs = [entry[0] for entry in fmap]
        seen: set[str] = set()
        for attr in compose_attrs:
            assert attr not in seen, f"{name} has duplicate compose_attr: {attr!r}"
            seen.add(attr)


# ---------------------------------------------------------------------------
# Specific field map content checks
# ---------------------------------------------------------------------------


class TestServiceFieldMap:
    """SERVICE_FIELD_MAP specific checks."""

    def test_has_image_entry(self) -> None:
        compose_attrs = [e[0] for e in SERVICE_FIELD_MAP]
        assert "image" in compose_attrs

    def test_has_ports_entry(self) -> None:
        compose_attrs = [e[0] for e in SERVICE_FIELD_MAP]
        assert "ports" in compose_attrs

    def test_has_volumes_entry(self) -> None:
        compose_attrs = [e[0] for e in SERVICE_FIELD_MAP]
        assert "volumes" in compose_attrs

    def test_has_environment_entry(self) -> None:
        compose_attrs = [e[0] for e in SERVICE_FIELD_MAP]
        assert "environment" in compose_attrs

    def test_has_healthcheck_entry(self) -> None:
        entries = {e[0]: e for e in SERVICE_FIELD_MAP}
        assert "healthcheck" in entries
        # healthcheck is a 1:N expansion (empty quadlet_attr)
        assert entries["healthcheck"][1] == ""

    def test_has_logging_entry(self) -> None:
        entries = {e[0]: e for e in SERVICE_FIELD_MAP}
        assert "logging" in entries
        # logging is a 1:N expansion (empty quadlet_attr)
        assert entries["logging"][1] == ""

    def test_volumes_is_expansion(self) -> None:
        entries = {e[0]: e for e in SERVICE_FIELD_MAP}
        assert "volumes" in entries
        assert entries["volumes"][1] == ""

    def test_all_converters_callable(self) -> None:
        for i, entry in enumerate(SERVICE_FIELD_MAP):
            if entry[2] is not None:
                assert callable(
                    entry[2]
                ), f"SERVICE_FIELD_MAP[{i}] converter not callable"


class TestBuildFieldMap:
    """BUILD_FIELD_MAP specific checks."""

    def test_has_context_entry(self) -> None:
        compose_attrs = [e[0] for e in BUILD_FIELD_MAP]
        assert "context" in compose_attrs

    def test_has_dockerfile_entry(self) -> None:
        compose_attrs = [e[0] for e in BUILD_FIELD_MAP]
        assert "dockerfile" in compose_attrs

    def test_has_target_entry(self) -> None:
        compose_attrs = [e[0] for e in BUILD_FIELD_MAP]
        assert "target" in compose_attrs

    def test_all_converters_callable(self) -> None:
        for i, entry in enumerate(BUILD_FIELD_MAP):
            if entry[2] is not None:
                assert callable(
                    entry[2]
                ), f"BUILD_FIELD_MAP[{i}] converter not callable"


class TestNetworkFieldMap:
    """NETWORK_FIELD_MAP specific checks."""

    def test_has_name_entry(self) -> None:
        compose_attrs = [e[0] for e in NETWORK_FIELD_MAP]
        assert "name" in compose_attrs

    def test_has_driver_entry(self) -> None:
        compose_attrs = [e[0] for e in NETWORK_FIELD_MAP]
        assert "driver" in compose_attrs

    def test_has_ipam_entry(self) -> None:
        entries = {e[0]: e for e in NETWORK_FIELD_MAP}
        assert "ipam" in entries
        # ipam is a 1:N expansion
        assert entries["ipam"][1] == ""

    def test_all_converters_callable(self) -> None:
        for i, entry in enumerate(NETWORK_FIELD_MAP):
            if entry[2] is not None:
                assert callable(
                    entry[2]
                ), f"NETWORK_FIELD_MAP[{i}] converter not callable"


class TestVolumeFieldMap:
    """VOLUME_FIELD_MAP specific checks."""

    def test_has_name_entry(self) -> None:
        compose_attrs = [e[0] for e in VOLUME_FIELD_MAP]
        assert "name" in compose_attrs

    def test_has_driver_entry(self) -> None:
        compose_attrs = [e[0] for e in VOLUME_FIELD_MAP]
        assert "driver" in compose_attrs

    def test_has_labels_entry(self) -> None:
        compose_attrs = [e[0] for e in VOLUME_FIELD_MAP]
        assert "labels" in compose_attrs

    def test_all_converters_callable(self) -> None:
        for i, entry in enumerate(VOLUME_FIELD_MAP):
            if entry[2] is not None:
                assert callable(
                    entry[2]
                ), f"VOLUME_FIELD_MAP[{i}] converter not callable"
