"""Tests for the compose→quadlet mapping layer (utils/mapping.py).

Covers:
- ``_apply_field_map`` — generic field map application
- ``map_service`` — Service → ContainerUnit
- ``map_build`` — ServiceBuild → BuildUnit
- ``map_network`` — Network → NetworkUnit
- ``map_volume`` — Volume → VolumeUnit
- ``QuadletBundle`` — aggregation, tagging, file rendering
- ``map_compose`` — end-to-end compose dict → QuadletBundle
"""

from pathlib import Path

import pytest
from pydantic import BaseModel

from models.compose import Network, Service, ServiceBuild, Volume
from models.quadlet.build import BuildUnit
from models.quadlet.container import ContainerUnit
from models.quadlet.network import NetworkUnit
from models.quadlet.pod import PodUnit
from models.quadlet.volume import VolumeUnit
from utils.field_maps import (
    BUILD_FIELD_MAP,
    NETWORK_FIELD_MAP,
    SERVICE_FIELD_MAP,
    VOLUME_FIELD_MAP,
)
from utils.mapping import (
    QuadletBundle,
    _apply_field_map,
    map_build,
    map_compose,
    map_network,
    map_service,
    map_volume,
)

# ---------------------------------------------------------------------------
# _apply_field_map
# ---------------------------------------------------------------------------


class TestApplyFieldMap:
    """Tests for the generic _apply_field_map helper."""

    def test_returns_empty_dict_for_empty_model(self) -> None:
        """A model with all-None fields should produce an empty dict."""

        class Src(BaseModel):
            x: str | None = None

        result = _apply_field_map(Src(), [("x", "X", None)])
        assert result == {}

    def test_identity_rename_no_converter(self) -> None:
        """Without a converter, the raw value is used directly."""

        class Src(BaseModel):
            x: str | None = None

        result = _apply_field_map(Src(x="hello"), [("x", "X", None)])
        assert result == {"X": "hello"}

    def test_converter_called(self) -> None:
        """Converter is invoked on the value."""

        class Src(BaseModel):
            val: int | None = None

        converter = lambda v: {"Result": str(v)}
        result = _apply_field_map(Src(val=42), [("val", "", converter)])
        assert result == {"Result": "42"}

    def test_converter_returns_empty_dict_skipped(self) -> None:
        """If converter returns an empty dict, nothing is added."""

        class Src(BaseModel):
            val: str | None = None

        converter = lambda v: {}
        result = _apply_field_map(Src(val="x"), [("val", "", converter)])
        assert result == {}

    def test_none_value_skipped(self) -> None:
        """None values should be skipped entirely."""

        class Src(BaseModel):
            x: str | None = None
            y: str | None = None

        result = _apply_field_map(
            Src(x=None, y="yes"),
            [("x", "X", None), ("y", "Y", None)],
        )
        assert result == {"Y": "yes"}

    def test_multiple_entries(self) -> None:
        """Multiple field map entries are all applied."""

        class Src(BaseModel):
            a: str | None = None
            b: int | None = None

        result = _apply_field_map(
            Src(a="alpha", b=42),
            [("a", "Alpha", None), ("b", "Beta", None)],
        )
        assert result == {"Alpha": "alpha", "Beta": 42}

    def test_1_to_n_expansion(self) -> None:
        """A converter returning multiple keys expands correctly."""

        class Src(BaseModel):
            data: str | None = None

        converter = lambda v: {"X": v, "Y": v.upper()}
        result = _apply_field_map(Src(data="hello"), [("data", "", converter)])
        assert result == {"X": "hello", "Y": "HELLO"}

    def test_missing_attribute_skipped(self) -> None:
        """If the source model doesn't have the attribute, it's skipped."""

        class Src(BaseModel):
            x: str | None = None

        result = _apply_field_map(Src(), [("nonexistent", "N", None)])
        assert result == {}


# ---------------------------------------------------------------------------
# map_service
# ---------------------------------------------------------------------------


class TestMapService:
    """Tests for map_service()."""

    def test_minimal_service(self) -> None:
        svc = Service.model_validate({"image": "nginx:latest"})
        unit = map_service(svc, service_name="web")
        assert isinstance(unit, ContainerUnit)
        assert unit.Image == "nginx:latest"
        assert unit.ContainerName == "web"

    def test_service_with_project_name(self) -> None:
        svc = Service.model_validate({"image": "nginx:latest"})
        unit = map_service(svc, service_name="web", project_name="myapp")
        assert unit.ContainerName == "myapp-web"

    def test_service_with_explicit_container_name(self) -> None:
        svc = Service.model_validate(
            {
                "image": "nginx:latest",
                "container_name": "custom-name",
            }
        )
        unit = map_service(svc, service_name="web", project_name="myapp")
        assert unit.ContainerName == "custom-name"

    def test_service_with_pod(self) -> None:
        svc = Service.model_validate({"image": "nginx:latest"})
        unit = map_service(svc, service_name="web", pod_name="myapp-pod")
        assert unit.Pod == "myapp-pod"

    def test_service_with_environment(self) -> None:
        svc = Service.model_validate(
            {
                "image": "nginx:latest",
                "environment": {"FOO": "bar"},
            }
        )
        unit = map_service(svc, service_name="web")
        assert unit.Environment is not None
        assert "FOO=bar" in unit.Environment

    def test_service_with_ports(self) -> None:
        svc = Service.model_validate(
            {
                "image": "nginx:latest",
                "ports": ["8080:80"],
            }
        )
        unit = map_service(svc, service_name="web")
        assert unit.PublishPort is not None
        assert "8080:80" in unit.PublishPort

    def test_service_with_healthcheck(self) -> None:
        svc = Service.model_validate(
            {
                "image": "nginx:latest",
                "healthcheck": {
                    "test": ["CMD", "curl", "-f", "http://localhost/"],
                    "interval": "30s",
                    "timeout": "10s",
                    "retries": 3,
                },
            }
        )
        unit = map_service(svc, service_name="web")
        assert unit.HealthCmd is not None
        assert unit.HealthInterval is not None
        assert unit.HealthRetries == 3

    def test_service_with_volumes(self) -> None:
        svc = Service.model_validate(
            {
                "image": "nginx:latest",
                "volumes": [
                    {"type": "bind", "source": "/host", "target": "/container"},
                ],
            }
        )
        unit = map_service(svc, service_name="web")
        assert unit.Volume is not None

    def test_service_no_image_no_build(self) -> None:
        """When no image and no build, service_name is used as Image."""
        svc = Service.model_validate({})
        unit = map_service(svc, service_name="web")
        assert unit.Image == "web"

    def test_service_with_labels(self) -> None:
        svc = Service.model_validate(
            {
                "image": "nginx:latest",
                "labels": {"com.example": "test"},
            }
        )
        unit = map_service(svc, service_name="web")
        assert unit.Label is not None
        assert any("com.example=test" in lbl for lbl in unit.Label)


# ---------------------------------------------------------------------------
# map_build
# ---------------------------------------------------------------------------


class TestMapBuild:
    """Tests for map_build()."""

    def test_minimal_build(self) -> None:
        build = ServiceBuild.model_validate({"context": "."})
        unit = map_build(build, service_name="web")
        assert isinstance(unit, BuildUnit)
        assert unit.ImageTag == "web"

    def test_build_with_project_name(self) -> None:
        build = ServiceBuild.model_validate({"context": "."})
        unit = map_build(build, service_name="web", project_name="myapp")
        assert unit.ImageTag == "myapp-web"

    def test_build_with_dockerfile(self) -> None:
        build = ServiceBuild.model_validate(
            {
                "context": ".",
                "dockerfile": "Dockerfile.custom",
            }
        )
        unit = map_build(build, service_name="web")
        assert unit.File == "Dockerfile.custom"

    def test_build_with_target(self) -> None:
        build = ServiceBuild.model_validate(
            {
                "context": ".",
                "target": "production",
            }
        )
        unit = map_build(build, service_name="web")
        assert unit.Target == "production"

    def test_build_with_labels(self) -> None:
        build = ServiceBuild.model_validate(
            {
                "context": ".",
                "labels": {"version": "1.0"},
            }
        )
        unit = map_build(build, service_name="web")
        assert unit.Label is not None
        assert any("version=1.0" in lbl for lbl in unit.Label)


# ---------------------------------------------------------------------------
# map_network
# ---------------------------------------------------------------------------


class TestMapNetwork:
    """Tests for map_network()."""

    def test_minimal_network(self) -> None:
        net = Network.model_validate({})
        unit = map_network(net, network_name="frontend")
        assert isinstance(unit, NetworkUnit)
        assert unit.NetworkName == "frontend"

    def test_network_with_project_name(self) -> None:
        net = Network.model_validate({})
        unit = map_network(net, network_name="frontend", project_name="myapp")
        assert unit.NetworkName == "myapp-frontend"

    def test_network_with_explicit_name(self) -> None:
        net = Network.model_validate({"name": "custom-net"})
        unit = map_network(net, network_name="frontend")
        assert unit.NetworkName == "custom-net"

    def test_network_with_driver(self) -> None:
        net = Network.model_validate({"driver": "bridge"})
        unit = map_network(net, network_name="frontend")
        assert unit.Driver == "bridge"

    def test_network_with_ipam(self) -> None:
        net = Network.model_validate(
            {
                "ipam": {
                    "driver": "default",
                    "config": [{"subnet": "172.20.0.0/16"}],
                },
            }
        )
        unit = map_network(net, network_name="frontend")
        assert unit.IPAMDriver == "default"
        assert unit.Subnet is not None
        assert "172.20.0.0/16" in unit.Subnet


# ---------------------------------------------------------------------------
# map_volume
# ---------------------------------------------------------------------------


class TestMapVolume:
    """Tests for map_volume()."""

    def test_minimal_volume(self) -> None:
        vol = Volume.model_validate({})
        unit = map_volume(vol, volume_name="data")
        assert isinstance(unit, VolumeUnit)
        assert unit.VolumeName == "data"

    def test_volume_with_project_name(self) -> None:
        vol = Volume.model_validate({})
        unit = map_volume(vol, volume_name="data", project_name="myapp")
        assert unit.VolumeName == "myapp-data"

    def test_volume_with_explicit_name(self) -> None:
        vol = Volume.model_validate({"name": "custom-vol"})
        unit = map_volume(vol, volume_name="data")
        assert unit.VolumeName == "custom-vol"

    def test_volume_with_driver(self) -> None:
        vol = Volume.model_validate({"driver": "local"})
        unit = map_volume(vol, volume_name="data")
        assert unit.Driver == "local"


# ---------------------------------------------------------------------------
# QuadletBundle
# ---------------------------------------------------------------------------


class TestQuadletBundle:
    """Tests for the QuadletBundle dataclass."""

    def test_empty_bundle(self) -> None:
        bundle = QuadletBundle()
        assert bundle.project_name == ""
        assert bundle.pod is None
        assert bundle.containers == []
        assert bundle.networks == []
        assert bundle.volumes == []
        assert bundle.builds == []

    def test_service_names_empty(self) -> None:
        bundle = QuadletBundle()
        assert bundle.service_names() == []

    def test_service_names_with_pod(self) -> None:
        bundle = QuadletBundle(pod=PodUnit(PodName="myapp"))
        names = bundle.service_names()
        # Quadlet: myapp.pod → myapp-pod.service
        assert "myapp-pod.service" in names

    def test_service_names_with_container(self) -> None:
        bundle = QuadletBundle(
            containers=[ContainerUnit(Image="nginx:latest", ContainerName="web")],
        )
        names = bundle.service_names()
        # Quadlet: web.container → web.service
        assert "web.service" in names

    def test_service_names_with_network(self) -> None:
        bundle = QuadletBundle(
            networks=[NetworkUnit(NetworkName="frontend")],
        )
        names = bundle.service_names()
        # Quadlet: frontend.network → frontend-network.service
        assert "frontend-network.service" in names

    def test_service_names_with_volume(self) -> None:
        bundle = QuadletBundle(
            volumes=[VolumeUnit(VolumeName="data")],
        )
        names = bundle.service_names()
        # Quadlet: data.volume → data-volume.service
        assert "data-volume.service" in names

    def test_service_names_with_build(self) -> None:
        bundle = QuadletBundle(
            builds=[BuildUnit(ImageTag="myapp-web")],
        )
        names = bundle.service_names()
        # Quadlet: myapp-web.build → myapp-web-build.service
        assert "myapp-web-build.service" in names

    def test_to_quadlet_files_empty(self) -> None:
        bundle = QuadletBundle()
        assert bundle.to_quadlet_files() == {}

    def test_to_quadlet_files_with_pod(self) -> None:
        bundle = QuadletBundle(pod=PodUnit(PodName="myapp"))
        files = bundle.to_quadlet_files()
        assert "myapp.pod" in files
        assert "[Pod]" in files["myapp.pod"]

    def test_to_quadlet_files_with_container(self) -> None:
        bundle = QuadletBundle(
            containers=[ContainerUnit(Image="nginx:latest", ContainerName="web")],
        )
        files = bundle.to_quadlet_files()
        assert "web.container" in files
        assert "[Container]" in files["web.container"]
        assert "Image=nginx:latest" in files["web.container"]

    def test_to_quadlet_files_with_network(self) -> None:
        bundle = QuadletBundle(
            networks=[NetworkUnit(NetworkName="frontend")],
        )
        files = bundle.to_quadlet_files()
        assert "frontend.network" in files
        assert "[Network]" in files["frontend.network"]

    def test_to_quadlet_files_with_volume(self) -> None:
        bundle = QuadletBundle(
            volumes=[VolumeUnit(VolumeName="data")],
        )
        files = bundle.to_quadlet_files()
        assert "data.volume" in files
        assert "[Volume]" in files["data.volume"]

    def test_to_quadlet_files_with_build(self) -> None:
        bundle = QuadletBundle(
            builds=[BuildUnit(ImageTag="myapp-web")],
        )
        files = bundle.to_quadlet_files()
        assert "myapp-web.build" in files
        assert "[Build]" in files["myapp-web.build"]

    def test_tag_injects_project_label(self) -> None:
        bundle = QuadletBundle(
            pod=PodUnit(PodName="test"),
            containers=[ContainerUnit(Image="nginx:latest", ContainerName="web")],
        )
        bundle._tag("myapp")
        label = "io.quadlet-compose.project=myapp"
        assert label in bundle.pod.Label  # type: ignore[union-attr]
        assert label in bundle.containers[0].Label  # type: ignore[index]

    def test_tag_appends_to_existing_labels(self) -> None:
        bundle = QuadletBundle(
            containers=[
                ContainerUnit(
                    Image="nginx:latest",
                    ContainerName="web",
                    Label=["existing=label"],
                )
            ],
        )
        bundle._tag("myapp")
        label = "io.quadlet-compose.project=myapp"
        assert "existing=label" in bundle.containers[0].Label  # type: ignore[index]
        assert label in bundle.containers[0].Label  # type: ignore[index]


# ---------------------------------------------------------------------------
# map_compose — end-to-end
# ---------------------------------------------------------------------------


class TestMapCompose:
    """Tests for the top-level map_compose() function."""

    def test_minimal_compose(self) -> None:
        data = {
            "services": {
                "web": {"image": "nginx:latest"},
            },
        }
        bundle = map_compose(data, project_name="test")
        assert bundle.project_name == "test"
        assert bundle.pod is not None
        assert bundle.pod.PodName == "test"
        assert len(bundle.containers) == 1
        assert bundle.containers[0].Image == "nginx:latest"
        assert bundle.containers[0].Pod == "test.pod"

    def test_compose_with_name(self) -> None:
        data = {
            "name": "myapp",
            "services": {
                "web": {"image": "nginx:latest"},
            },
        }
        bundle = map_compose(data)
        assert bundle.project_name == "myapp"

    def test_compose_with_networks(self) -> None:
        data = {
            "services": {"web": {"image": "nginx:latest"}},
            "networks": {
                "frontend": {"driver": "bridge"},
                "backend": None,
            },
        }
        bundle = map_compose(data, project_name="test")
        assert len(bundle.networks) == 2
        net_names = [n.NetworkName for n in bundle.networks]
        assert "test-frontend" in net_names
        assert "test-backend" in net_names

    def test_compose_with_volumes(self) -> None:
        data = {
            "services": {"web": {"image": "nginx:latest"}},
            "volumes": {
                "data": {"driver": "local"},
            },
        }
        bundle = map_compose(data, project_name="test")
        assert len(bundle.volumes) == 1
        assert bundle.volumes[0].VolumeName == "test-data"

    def test_compose_with_build(self) -> None:
        data = {
            "services": {
                "web": {
                    "build": {"context": ".", "dockerfile": "Dockerfile"},
                },
            },
        }
        bundle = map_compose(data, project_name="test")
        assert len(bundle.builds) == 1
        assert bundle.builds[0].ImageTag == "test-web"

    def test_compose_with_build_string(self) -> None:
        """build: can be a plain string (shorthand for context)."""
        data = {
            "services": {
                "web": {"build": "."},
            },
        }
        bundle = map_compose(data, project_name="test")
        assert len(bundle.builds) == 1

    def test_compose_skips_external_networks(self) -> None:
        data = {
            "services": {"web": {"image": "nginx:latest"}},
            "networks": {
                "external_net": {"external": True},
            },
        }
        bundle = map_compose(data, project_name="test")
        assert len(bundle.networks) == 0

    def test_compose_skips_external_volumes(self) -> None:
        data = {
            "services": {"web": {"image": "nginx:latest"}},
            "volumes": {
                "ext_vol": {"external": True},
            },
        }
        bundle = map_compose(data, project_name="test")
        assert len(bundle.volumes) == 0

    def test_compose_project_name_from_path(self) -> None:
        data = {"services": {"web": {"image": "nginx:latest"}}}
        compose_path = Path("/home/user/myproject/docker-compose.yml")
        bundle = map_compose(data, compose_path=compose_path)
        assert bundle.project_name == "myproject"

    def test_compose_project_name_default(self) -> None:
        data = {"services": {"web": {"image": "nginx:latest"}}}
        bundle = map_compose(data)
        assert bundle.project_name == "default"

    def test_compose_explicit_project_name_overrides(self) -> None:
        data = {
            "name": "fromcompose",
            "services": {"web": {"image": "nginx:latest"}},
        }
        bundle = map_compose(data, project_name="explicit")
        assert bundle.project_name == "explicit"

    def test_compose_tags_all_units(self) -> None:
        data = {
            "services": {"web": {"image": "nginx:latest"}},
            "networks": {"frontend": None},
            "volumes": {"data": {}},
        }
        bundle = map_compose(data, project_name="test")
        label = "io.quadlet-compose.project=test"
        assert label in bundle.pod.Label  # type: ignore[union-attr]
        assert label in bundle.containers[0].Label  # type: ignore[index]
        assert label in bundle.networks[0].Label  # type: ignore[index]
        assert label in bundle.volumes[0].Label  # type: ignore[index]

    def test_compose_full_round_trip(self, sample_compose_full: dict) -> None:
        """Full compose dict → QuadletBundle → quadlet files round-trip."""
        bundle = map_compose(sample_compose_full, project_name="myapp")
        files = bundle.to_quadlet_files()

        # Should have pod, container(s), network(s), volume(s)
        assert any(f.endswith(".pod") for f in files)
        assert any(f.endswith(".container") for f in files)
        assert any(f.endswith(".network") for f in files)
        assert any(f.endswith(".volume") for f in files)

        # Each file should start with its section header
        for filename, content in files.items():
            assert content.startswith(
                "["
            ), f"{filename} doesn't start with section header"

    def test_compose_pod_exit_policy(self) -> None:
        data = {"services": {"web": {"image": "nginx:latest"}}}
        bundle = map_compose(data, project_name="test")
        assert bundle.pod is not None
        assert bundle.pod.ExitPolicy == "stop"

    def test_compose_multiple_services(self) -> None:
        data = {
            "services": {
                "web": {"image": "nginx:latest"},
                "db": {"image": "postgres:15"},
            },
        }
        bundle = map_compose(data, project_name="test")
        assert len(bundle.containers) == 2
        images = [c.Image for c in bundle.containers]
        assert "nginx:latest" in images
        assert "postgres:15" in images
