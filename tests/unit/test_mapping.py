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
    _render_with_hash,
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
        assert unit.Image == "docker.io/library/nginx:latest"
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

    def test_service_with_bind_mount(self) -> None:
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
        assert unit.Volume == ["/host:/container"]

    def test_service_with_named_volume(self) -> None:
        svc = Service.model_validate(
            {
                "image": "nginx:latest",
                "volumes": [
                    {"type": "volume", "source": "data", "target": "/data"},
                ],
            }
        )
        unit = map_service(svc, service_name="web")
        assert unit.Volume is not None
        assert unit.Volume == ["data:/data"]

    def test_service_no_image_no_build(self) -> None:
        """When no image and no build, service_name gets localhost/ prefix."""
        svc = Service.model_validate({})
        unit = map_service(svc, service_name="web")
        assert unit.Image == "localhost/web"

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

    def test_service_with_userns_mode(self) -> None:
        svc = Service.model_validate(
            {
                "image": "nginx:latest",
                "userns_mode": "host",
            }
        )
        unit = map_service(svc, service_name="web")
        assert unit.UserNS == "host"

    def test_service_without_userns_mode(self) -> None:
        svc = Service.model_validate({"image": "nginx:latest"})
        unit = map_service(svc, service_name="web")
        assert unit.UserNS is None

    def test_service_with_env_file_string(self) -> None:
        svc = Service.model_validate(
            {
                "image": "nginx:latest",
                "env_file": ".env",
            }
        )
        unit = map_service(svc, service_name="web")
        assert unit.EnvironmentFile == [".env"]

    def test_service_with_env_file_list(self) -> None:
        svc = Service.model_validate(
            {
                "image": "nginx:latest",
                "env_file": [".env", "overrides.env"],
            }
        )
        unit = map_service(svc, service_name="web")
        assert unit.EnvironmentFile == [".env", "overrides.env"]

    def test_service_with_env_file_objects(self) -> None:
        svc = Service.model_validate(
            {
                "image": "nginx:latest",
                "env_file": [
                    {"path": ".env", "required": True},
                    {"path": "prod.env"},
                ],
            }
        )
        unit = map_service(svc, service_name="web")
        assert unit.EnvironmentFile == [".env", "prod.env"]

    def test_service_without_env_file(self) -> None:
        svc = Service.model_validate({"image": "nginx:latest"})
        unit = map_service(svc, service_name="web")
        assert unit.EnvironmentFile is None


# ---------------------------------------------------------------------------
# map_build
# ---------------------------------------------------------------------------


class TestMapBuild:
    """Tests for map_build()."""

    def test_minimal_build(self) -> None:
        build = ServiceBuild.model_validate({"context": "."})
        unit = map_build(build, service_name="web")
        assert isinstance(unit, BuildUnit)
        assert unit.ImageTag == "localhost/web"

    def test_build_with_project_name(self) -> None:
        build = ServiceBuild.model_validate({"context": "."})
        unit = map_build(build, service_name="web", project_name="myapp")
        assert unit.ImageTag == "localhost/myapp-web"

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

    def test_service_names_with_build_slash_in_tag(self) -> None:
        """ImageTag with '/' (e.g. 'localhost/myapp-web') must produce
        a valid service name without directory separators."""
        bundle = QuadletBundle(
            builds=[BuildUnit(ImageTag="localhost/myapp-web")],
        )
        names = bundle.service_names()
        assert "localhost_myapp-web-build.service" in names

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

    def test_to_quadlet_files_with_build_sanitises_slash(self) -> None:
        """ImageTag may contain '/' (e.g. 'localhost/myapp-web') — the
        filename must replace it to avoid creating subdirectories."""
        bundle = QuadletBundle(
            builds=[BuildUnit(ImageTag="localhost/myapp-web")],
        )
        files = bundle.to_quadlet_files()
        # '/' replaced with '_' in filename
        assert "localhost_myapp-web.build" in files
        # ImageTag value inside the file is unchanged
        assert "ImageTag=localhost/myapp-web" in files["localhost_myapp-web.build"]

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
        assert bundle.containers[0].Image == "docker.io/library/nginx:latest"
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
        assert bundle.builds[0].ImageTag == "localhost/test-web"

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
        assert "docker.io/library/nginx:latest" in images
        assert "docker.io/library/postgres:15" in images

    def test_compose_restart_always_adds_install(self) -> None:
        """Services with restart: always should get [Install] WantedBy."""
        data = {
            "services": {
                "web": {"image": "nginx:latest", "restart": "always"},
            },
        }
        bundle = map_compose(data, project_name="test")
        container = bundle.containers[0]
        assert container.install == {"WantedBy": "default.target"}
        # Verify it appears in the rendered quadlet file
        files = bundle.to_quadlet_files()
        content = files["test-web.container"]
        assert "[Install]" in content
        assert "WantedBy=default.target" in content

    def test_compose_restart_unless_stopped_adds_install(self) -> None:
        """Services with restart: unless-stopped should get [Install] WantedBy."""
        data = {
            "services": {
                "web": {"image": "nginx:latest", "restart": "unless-stopped"},
            },
        }
        bundle = map_compose(data, project_name="test")
        container = bundle.containers[0]
        assert container.install == {"WantedBy": "default.target"}

    def test_compose_restart_on_failure_no_install(self) -> None:
        """Services with restart: on-failure should NOT get [Install]."""
        data = {
            "services": {
                "web": {"image": "nginx:latest", "restart": "on-failure"},
            },
        }
        bundle = map_compose(data, project_name="test")
        container = bundle.containers[0]
        assert container.install is None

    def test_compose_no_restart_no_install(self) -> None:
        """Services without restart should NOT get [Install]."""
        data = {
            "services": {
                "web": {"image": "nginx:latest"},
            },
        }
        bundle = map_compose(data, project_name="test")
        container = bundle.containers[0]
        assert container.install is None

    def test_compose_container_service_overrides_exec_stop_post(self) -> None:
        """All containers should get ExecStopPost= to prevent auto-removal."""
        data = {
            "services": {
                "web": {"image": "nginx:latest"},
            },
        }
        bundle = map_compose(data, project_name="test")
        container = bundle.containers[0]
        assert container.service == {"ExecStopPost": ""}
        # Verify it appears in the rendered quadlet file
        files = bundle.to_quadlet_files()
        content = files["test-web.container"]
        assert "[Service]" in content
        assert "ExecStopPost=" in content

    def test_compose_service_section_with_install(self) -> None:
        """[Service] and [Install] sections should both render when present."""
        data = {
            "services": {
                "web": {"image": "nginx:latest", "restart": "always"},
            },
        }
        bundle = map_compose(data, project_name="test")
        container = bundle.containers[0]
        assert container.service == {"ExecStopPost": ""}
        assert container.install == {"WantedBy": "default.target"}
        files = bundle.to_quadlet_files()
        content = files["test-web.container"]
        assert "[Service]" in content
        assert "ExecStopPost=" in content
        assert "[Install]" in content
        assert "WantedBy=default.target" in content

    def test_port_deduplication_across_services(self) -> None:
        """Duplicate PublishPort values from different services are deduplicated on the pod."""
        data = {
            "services": {
                "web": {"image": "nginx:latest", "ports": ["8080:80"]},
                "api": {"image": "myapi:latest", "ports": ["8080:80", "9090:90"]},
            },
        }
        bundle = map_compose(data, project_name="test")
        assert bundle.pod is not None
        pod_ports = bundle.pod.PublishPort
        assert pod_ports is not None
        assert (
            pod_ports.count("8080:80") == 1
        ), f'Expected exactly one "8080:80", got {pod_ports}'
        assert "9090:90" in pod_ports
        # Container units should have PublishPort cleared
        for c in bundle.containers:
            assert c.PublishPort is None

    def test_userns_migrated_to_pod(self) -> None:
        """UserNS is moved from container to pod (Podman forbids it on containers in pods)."""
        data = {
            "services": {
                "web": {"image": "nginx:latest", "userns_mode": "host"},
            },
        }
        bundle = map_compose(data, project_name="test")
        assert bundle.pod is not None
        assert bundle.pod.UserNS == "host"
        # Container should have UserNS cleared
        for c in bundle.containers:
            assert c.UserNS is None

    def test_userns_conflict_raises_error(self) -> None:
        """Conflicting userns_mode values across services raises ComposeError."""
        from utils import ComposeError

        data = {
            "services": {
                "web": {"image": "nginx:latest", "userns_mode": "host"},
                "api": {"image": "myapi:latest", "userns_mode": "private"},
            },
        }
        with pytest.raises(ComposeError, match="Conflicting userns_mode"):
            map_compose(data, project_name="test")

    def test_userns_same_value_no_error(self) -> None:
        """Same userns_mode across services is fine — set once on the pod."""
        data = {
            "services": {
                "web": {"image": "nginx:latest", "userns_mode": "host"},
                "api": {"image": "myapi:latest", "userns_mode": "host"},
            },
        }
        bundle = map_compose(data, project_name="test")
        assert bundle.pod is not None
        assert bundle.pod.UserNS == "host"
        for c in bundle.containers:
            assert c.UserNS is None

    def test_bind_mount_relative_path_resolution(self) -> None:
        """Relative bind mount sources are resolved against the compose file directory."""
        data = {
            "services": {
                "web": {
                    "image": "nginx:latest",
                    "volumes": ["./data:/app/data", "../config:/etc/app"],
                },
            },
        }
        compose_path = Path("/home/user/myproject/docker-compose.yml")
        bundle = map_compose(data, project_name="test", compose_path=compose_path)
        container = bundle.containers[0]
        assert container.Volume is not None
        assert len(container.Volume) == 2
        # Use sets for comparison because compose-spec volumes are stored
        # as a set (unordered).
        assert set(container.Volume) == {
            "/home/user/myproject/data:/app/data",
            "/home/user/config:/etc/app",
        }

    def test_bind_mount_absolute_path_unchanged(self) -> None:
        """Absolute bind mount sources are not modified."""
        data = {
            "services": {
                "web": {
                    "image": "nginx:latest",
                    "volumes": ["/host/path:/container/path"],
                },
            },
        }
        compose_path = Path("/home/user/myproject/docker-compose.yml")
        bundle = map_compose(data, project_name="test", compose_path=compose_path)
        container = bundle.containers[0]
        assert container.Volume is not None
        assert container.Volume == ["/host/path:/container/path"]

    def test_named_volume_not_resolved(self) -> None:
        """Named volumes should not have path resolution applied."""
        data = {
            "services": {
                "web": {
                    "image": "nginx:latest",
                    "volumes": ["myvolume:/data"],
                },
            },
        }
        compose_path = Path("/home/user/myproject/docker-compose.yml")
        bundle = map_compose(data, project_name="test", compose_path=compose_path)
        container = bundle.containers[0]
        assert container.Volume is not None
        assert container.Volume == ["myvolume:/data"]

    # -- Build context relative path resolution --------------------------------

    def test_build_context_relative_path_resolution(self) -> None:
        """Relative build context is resolved against the compose file directory."""
        data = {
            "services": {
                "web": {
                    "build": {"context": "./app", "dockerfile": "Dockerfile"},
                },
            },
        }
        compose_path = Path("/home/user/myproject/docker-compose.yml")
        bundle = map_compose(data, project_name="test", compose_path=compose_path)
        assert len(bundle.builds) == 1
        assert bundle.builds[0].SetWorkingDirectory == "/home/user/myproject/app"

    def test_build_context_parent_relative_path_resolution(self) -> None:
        """Build context with ``../`` is resolved against the compose file directory."""
        data = {
            "services": {
                "web": {
                    "build": {"context": "../shared/app"},
                },
            },
        }
        compose_path = Path("/home/user/myproject/docker-compose.yml")
        bundle = map_compose(data, project_name="test", compose_path=compose_path)
        assert len(bundle.builds) == 1
        assert bundle.builds[0].SetWorkingDirectory == "/home/user/shared/app"

    def test_build_context_absolute_path_unchanged(self) -> None:
        """Absolute build context paths are not modified."""
        data = {
            "services": {
                "web": {
                    "build": {"context": "/opt/myapp"},
                },
            },
        }
        compose_path = Path("/home/user/myproject/docker-compose.yml")
        bundle = map_compose(data, project_name="test", compose_path=compose_path)
        assert len(bundle.builds) == 1
        assert bundle.builds[0].SetWorkingDirectory == "/opt/myapp"

    def test_build_context_string_relative_resolution(self) -> None:
        """Shorthand build (string) with relative path is resolved."""
        data = {
            "services": {
                "web": {
                    "build": "./webapp",
                },
            },
        }
        compose_path = Path("/home/user/myproject/docker-compose.yml")
        bundle = map_compose(data, project_name="test", compose_path=compose_path)
        assert len(bundle.builds) == 1
        assert bundle.builds[0].SetWorkingDirectory == "/home/user/myproject/webapp"

    def test_env_file_relative_path_resolution(self) -> None:
        """Relative env_file paths are resolved against the compose file directory."""
        data = {
            "services": {
                "web": {
                    "image": "nginx:latest",
                    "env_file": ["./envs/.env", "../shared.env"],
                },
            },
        }
        compose_path = Path("/home/user/myproject/docker-compose.yml")
        bundle = map_compose(data, project_name="test", compose_path=compose_path)
        container = bundle.containers[0]
        assert container.EnvironmentFile == [
            "/home/user/myproject/envs/.env",
            "/home/user/shared.env",
        ]

    def test_env_file_absolute_path_unchanged(self) -> None:
        """Absolute env_file paths are not modified."""
        data = {
            "services": {
                "web": {
                    "image": "nginx:latest",
                    "env_file": ["/etc/app/.env"],
                },
            },
        }
        compose_path = Path("/home/user/myproject/docker-compose.yml")
        bundle = map_compose(data, project_name="test", compose_path=compose_path)
        container = bundle.containers[0]
        assert container.EnvironmentFile == ["/etc/app/.env"]

    def test_env_file_bare_filename_resolved(self) -> None:
        """Bare filename env_file (no path prefix) is resolved to absolute."""
        data = {
            "services": {
                "web": {
                    "image": "nginx:latest",
                    "env_file": [".env"],
                },
            },
        }
        compose_path = Path("/home/user/myproject/docker-compose.yml")
        bundle = map_compose(data, project_name="test", compose_path=compose_path)
        container = bundle.containers[0]
        assert container.EnvironmentFile == ["/home/user/myproject/.env"]


# ---------------------------------------------------------------------------
# _render_with_hash / hash label in to_quadlet_files
# ---------------------------------------------------------------------------


class TestRenderWithHash:
    """Tests for the _render_with_hash helper and hash label in to_quadlet_files."""

    def test_includes_hash_label(self) -> None:
        unit = ContainerUnit(Image="nginx:latest", ContainerName="web")
        result = _render_with_hash(unit)
        assert "Label=io.quadlet-compose.hash=" in result

    def test_hash_is_deterministic(self) -> None:
        unit = ContainerUnit(Image="nginx:latest", ContainerName="web")
        result_a = _render_with_hash(unit)
        result_b = _render_with_hash(unit)
        assert result_a == result_b

    def test_hash_changes_with_content(self) -> None:
        unit_a = ContainerUnit(Image="nginx:latest", ContainerName="web")
        unit_b = ContainerUnit(Image="postgres:15", ContainerName="db")
        result_a = _render_with_hash(unit_a)
        result_b = _render_with_hash(unit_b)
        assert result_a != result_b

    def test_hash_is_64_char_hex(self) -> None:
        unit = ContainerUnit(Image="nginx:latest", ContainerName="web")
        result = _render_with_hash(unit)
        prefix = "Label=io.quadlet-compose.hash="
        hash_line = [l for l in result.splitlines() if l.startswith(prefix)][0]
        digest = hash_line[len(prefix) :]
        assert len(digest) == 64
        assert all(c in "0123456789abcdef" for c in digest)

    def test_hash_label_in_container_section_not_install(self) -> None:
        """Hash label must appear in [Container], not in [Install]."""
        unit = ContainerUnit(
            Image="nginx:latest",
            ContainerName="web",
            install={"WantedBy": "default.target"},
        )
        result = _render_with_hash(unit)
        lines = result.splitlines()
        in_install = False
        hash_in_install = False
        hash_in_container = False
        for line in lines:
            if line == "[Install]":
                in_install = True
            elif line.startswith("["):
                in_install = False
            if line.startswith("Label=io.quadlet-compose.hash="):
                if in_install:
                    hash_in_install = True
                else:
                    hash_in_container = True
        assert hash_in_container, "Hash label should be in [Container] section"
        assert not hash_in_install, "Hash label must NOT be in [Install] section"

    def test_to_quadlet_files_includes_hash(self) -> None:
        bundle = QuadletBundle(
            containers=[ContainerUnit(Image="nginx:latest", ContainerName="web")],
        )
        files = bundle.to_quadlet_files()
        content = files["web.container"]
        assert "Label=io.quadlet-compose.hash=" in content

    def test_to_quadlet_files_hash_matches_render_with_hash(self) -> None:
        """The hash in to_quadlet_files output matches _render_with_hash."""
        unit = ContainerUnit(Image="nginx:latest", ContainerName="web")
        bundle = QuadletBundle(containers=[unit])
        files = bundle.to_quadlet_files()
        # _render_with_hash was already called by to_quadlet_files, so
        # the unit now has the hash label.  Re-rendering should produce
        # the same result (idempotent).
        assert files["web.container"] == _render_with_hash(unit)


# ---------------------------------------------------------------------------
# Named volume → .volume unit file referencing
# ---------------------------------------------------------------------------


class TestNamedVolumeReferencing:
    """Tests for rewriting container Volume= to reference .volume unit files."""

    def test_named_volume_references_volume_file(self) -> None:
        """A named volume in a service should reference the .volume unit file."""
        compose = {
            "name": "myapp",
            "services": {
                "db": {
                    "image": "postgres:15",
                    "volumes": ["dbdata:/var/lib/postgresql/data"],
                },
            },
            "volumes": {
                "dbdata": {},
            },
        }
        bundle = map_compose(compose)
        container = bundle.containers[0]

        # The container should reference the .volume file, not the raw name
        assert container.Volume is not None
        assert any(
            v.startswith("myapp-dbdata.volume:") for v in container.Volume
        ), f"Expected .volume reference, got: {container.Volume}"

    def test_named_volume_unit_created(self) -> None:
        """A .volume unit file should be created for declared volumes."""
        compose = {
            "name": "myapp",
            "services": {
                "db": {
                    "image": "postgres:15",
                    "volumes": ["dbdata:/var/lib/postgresql/data"],
                },
            },
            "volumes": {
                "dbdata": {},
            },
        }
        bundle = map_compose(compose)
        assert len(bundle.volumes) == 1
        assert bundle.volumes[0].VolumeName == "myapp-dbdata"

    def test_bind_mount_not_rewritten(self) -> None:
        """Bind mounts should NOT be rewritten to .volume references."""
        compose = {
            "name": "myapp",
            "services": {
                "web": {
                    "image": "nginx:latest",
                    "volumes": ["./html:/usr/share/nginx/html:ro"],
                },
            },
        }
        bundle = map_compose(compose)
        container = bundle.containers[0]

        assert container.Volume is not None
        # Bind mount should keep its original source (resolved to absolute)
        assert any(
            "/html:/usr/share/nginx/html:ro" in v for v in container.Volume
        ), f"Bind mount should not be rewritten, got: {container.Volume}"

    def test_external_volume_not_rewritten(self) -> None:
        """External volumes should NOT create .volume files or rewrite references."""
        compose = {
            "name": "myapp",
            "services": {
                "db": {
                    "image": "postgres:15",
                    "volumes": ["ext_data:/var/lib/postgresql/data"],
                },
            },
            "volumes": {
                "ext_data": {"external": True},
            },
        }
        bundle = map_compose(compose)
        container = bundle.containers[0]

        # No volume unit should be created for external volumes
        assert len(bundle.volumes) == 0

        # Container should keep the raw volume name (not rewritten)
        assert container.Volume is not None
        assert any(
            v.startswith("ext_data:") for v in container.Volume
        ), f"External volume should not be rewritten, got: {container.Volume}"

    def test_undeclared_volume_not_rewritten(self) -> None:
        """A volume used in a service but not in top-level volumes: should not be rewritten."""
        compose = {
            "name": "myapp",
            "services": {
                "db": {
                    "image": "postgres:15",
                    "volumes": ["auto_data:/var/lib/postgresql/data"],
                },
            },
        }
        bundle = map_compose(compose)
        container = bundle.containers[0]

        # No volume unit created (not declared in top-level volumes)
        assert len(bundle.volumes) == 0

        # Container keeps the raw name (Podman will auto-create)
        assert container.Volume is not None
        assert any(
            v.startswith("auto_data:") for v in container.Volume
        ), f"Undeclared volume should not be rewritten, got: {container.Volume}"

    def test_volume_reference_in_quadlet_files(self) -> None:
        """The generated .container file should contain the .volume reference."""
        compose = {
            "name": "myapp",
            "services": {
                "db": {
                    "image": "postgres:15",
                    "volumes": ["dbdata:/var/lib/postgresql/data"],
                },
            },
            "volumes": {
                "dbdata": {},
            },
        }
        bundle = map_compose(compose)
        files = bundle.to_quadlet_files()

        container_content = files["myapp-db.container"]
        assert (
            "Volume=myapp-dbdata.volume:/var/lib/postgresql/data" in container_content
        )

        # The .volume file should also exist
        assert "myapp-dbdata.volume" in files
