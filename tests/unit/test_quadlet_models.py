"""Tests for Quadlet unit models (models/quadlet/).

Covers:
- ``QuadletUnit`` base class (``_coerce_list`` validator, ``to_quadlet()`` serializer)
- ``ContainerUnit`` — field population and serialisation
- ``PodUnit`` — field population and serialisation
- ``NetworkUnit`` — field population and serialisation
- ``VolumeUnit`` — field population and serialisation
- ``BuildUnit`` — field population and serialisation
"""

import pytest

from models.quadlet._base import QuadletUnit, _is_list_annotation
from models.quadlet.build import BuildUnit
from models.quadlet.container import ContainerUnit
from models.quadlet.network import NetworkUnit
from models.quadlet.pod import PodUnit
from models.quadlet.volume import VolumeUnit

# ---------------------------------------------------------------------------
# _is_list_annotation helper
# ---------------------------------------------------------------------------


class TestIsListAnnotation:
    """Tests for the _is_list_annotation helper."""

    def test_plain_list(self) -> None:
        from typing import get_type_hints, List

        assert _is_list_annotation(list[str]) is True

    def test_optional_list(self) -> None:
        from typing import get_args

        ann = list[str] | None
        assert _is_list_annotation(ann) is True

    def test_plain_str(self) -> None:
        assert _is_list_annotation(str) is False

    def test_optional_str(self) -> None:
        assert _is_list_annotation(str | None) is False

    def test_int(self) -> None:
        assert _is_list_annotation(int) is False


# ---------------------------------------------------------------------------
# QuadletUnit base — _coerce_list
# ---------------------------------------------------------------------------


class TestCoerceList:
    """Tests for the _coerce_list validator on QuadletUnit."""

    def test_str_coerced_to_list_for_list_field(self) -> None:
        """A bare string should be wrapped in a list for list[str] | None fields."""
        unit = ContainerUnit(Image="nginx:latest", DNS="8.8.8.8")
        assert unit.DNS == ["8.8.8.8"]

    def test_list_preserved_for_list_field(self) -> None:
        """A list should be passed through unchanged."""
        unit = ContainerUnit(Image="nginx:latest", DNS=["8.8.8.8", "8.8.4.4"])
        assert unit.DNS == ["8.8.8.8", "8.8.4.4"]

    def test_none_preserved_for_list_field(self) -> None:
        """None should be preserved as None."""
        unit = ContainerUnit(Image="nginx:latest", DNS=None)
        assert unit.DNS is None

    def test_str_not_coerced_for_scalar_field(self) -> None:
        """Scalar fields should not be affected by _coerce_list."""
        unit = ContainerUnit(Image="nginx:latest", HostName="myhost")
        assert unit.HostName == "myhost"
        assert isinstance(unit.HostName, str)


# ---------------------------------------------------------------------------
# QuadletUnit base — to_quadlet()
# ---------------------------------------------------------------------------


class TestToQuadlet:
    """Tests for the to_quadlet() serializer."""

    def test_minimal_container(self) -> None:
        unit = ContainerUnit(Image="nginx:latest")
        result = unit.to_quadlet()
        assert result.startswith("[Container]")
        assert "Image=nginx:latest" in result

    def test_none_fields_omitted(self) -> None:
        unit = ContainerUnit(Image="nginx:latest")
        result = unit.to_quadlet()
        assert "HostName=" not in result
        assert "Pod=" not in result
        assert "Environment=" not in result

    def test_scalar_field_rendered(self) -> None:
        unit = ContainerUnit(Image="nginx:latest", HostName="myhost")
        result = unit.to_quadlet()
        assert "HostName=myhost" in result

    def test_list_field_multi_line(self) -> None:
        unit = ContainerUnit(
            Image="nginx:latest",
            DNS=["8.8.8.8", "8.8.4.4"],
        )
        result = unit.to_quadlet()
        assert "DNS=8.8.8.8" in result
        assert "DNS=8.8.4.4" in result

    def test_empty_list_omitted(self) -> None:
        unit = ContainerUnit(Image="nginx:latest", DNS=[])
        result = unit.to_quadlet()
        assert "DNS=" not in result

    def test_no_trailing_newline(self) -> None:
        unit = ContainerUnit(Image="nginx:latest")
        result = unit.to_quadlet()
        assert not result.endswith("\n")

    def test_install_section_appended(self) -> None:
        """When install is set, [Install] section should appear after [Container]."""
        unit = ContainerUnit(
            Image="nginx:latest",
            install={"WantedBy": "default.target"},
        )
        result = unit.to_quadlet()
        assert "[Container]" in result
        assert "\n\n[Install]\nWantedBy=default.target" in result

    def test_install_section_absent_when_none(self) -> None:
        """When install is None (default), no [Install] section should appear."""
        unit = ContainerUnit(Image="nginx:latest")
        result = unit.to_quadlet()
        assert "[Install]" not in result

    def test_install_section_absent_when_empty(self) -> None:
        """When install is an empty dict, no [Install] section should appear."""
        unit = ContainerUnit(Image="nginx:latest", install={})
        result = unit.to_quadlet()
        assert "[Install]" not in result


# ---------------------------------------------------------------------------
# ContainerUnit
# ---------------------------------------------------------------------------


class TestContainerUnit:
    """Tests for ContainerUnit-specific fields."""

    def test_image_required(self) -> None:
        unit = ContainerUnit(Image="nginx:latest")
        assert unit.Image == "nginx:latest"

    def test_image_missing_raises(self) -> None:
        with pytest.raises(Exception):
            ContainerUnit()  # type: ignore[call-arg]

    def test_all_scalar_fields(self) -> None:
        unit = ContainerUnit(
            Image="nginx:latest",
            ContainerName="web",
            HostName="myhost",
            Entrypoint="/entrypoint.sh",
            WorkingDir="/app",
            User="appuser",
            Group="appgroup",
            IP="10.0.0.1",
            IP6="::1",
            LogDriver="json-file",
            Memory="512m",
            PidsLimit=100,
            Pod="myapp-pod",
            Pull="always",
            ReadOnly=True,
            ReadOnlyTmpfs=True,
            RunInit=True,
            ShmSize="64m",
            StopSignal="SIGTERM",
            StopTimeout=30,
            Timezone="UTC",
        )
        assert unit.ContainerName == "web"
        assert unit.HostName == "myhost"
        assert unit.Memory == "512m"
        assert unit.Pod == "myapp-pod"

    def test_all_list_fields(self) -> None:
        unit = ContainerUnit(
            Image="nginx:latest",
            AddCapability=["NET_ADMIN"],
            DropCapability=["MKNOD"],
            AddDevice=["/dev/sda:/dev/xvda"],
            AddHost=["myhost:1.2.3.4"],
            Annotation=["anno=val"],
            Label=["label=val"],
            DNS=["8.8.8.8"],
            DNSOption=["ndots:5"],
            DNSSearch=["example.com"],
            Environment=["FOO=bar"],
            ExposeHostPort=["8080"],
            PublishPort=["80:80"],
            GroupAdd=["dialout"],
            Mount=["type=bind,src=/h,dst=/c"],
            Network=["frontend"],
            Secret=["mysecret"],
            Sysctl=["net.core.somaxconn=1024"],
            Tmpfs=["/run"],
            Ulimit=["nofile=65536"],
            Volume=["data:/data"],
        )
        assert unit.AddCapability == ["NET_ADMIN"]
        assert unit.PublishPort == ["80:80"]
        assert unit.Volume == ["data:/data"]

    def test_bool_fields(self) -> None:
        unit = ContainerUnit(
            Image="nginx:latest",
            RunInit=True,
            ReadOnly=True,
            HttpProxy=True,
            NoNewPrivileges=True,
        )
        assert unit.RunInit is True
        assert unit.ReadOnly is True

    def test_int_fields(self) -> None:
        unit = ContainerUnit(
            Image="nginx:latest",
            PidsLimit=100,
            StopTimeout=30,
            HealthRetries=3,
            HealthMaxLogCount=5,
        )
        assert unit.PidsLimit == 100
        assert unit.StopTimeout == 30
        assert unit.HealthRetries == 3

    def test_literal_fields(self) -> None:
        unit = ContainerUnit(
            Image="nginx:latest",
            Pull="always",
            CgroupsMode="enabled",
            AutoUpdate="registry",
            Notify="healthy",
            HealthOnFailure="restart",
        )
        assert unit.Pull == "always"
        assert unit.CgroupsMode == "enabled"

    def test_to_quadlet_section_header(self) -> None:
        unit = ContainerUnit(Image="nginx:latest")
        assert unit.to_quadlet().startswith("[Container]")


# ---------------------------------------------------------------------------
# PodUnit
# ---------------------------------------------------------------------------


class TestPodUnit:
    """Tests for PodUnit."""

    def test_minimal(self) -> None:
        unit = PodUnit(PodName="myapp")
        assert unit.PodName == "myapp"

    def test_with_exit_policy(self) -> None:
        unit = PodUnit(PodName="myapp", ExitPolicy="stop")
        assert unit.ExitPolicy == "stop"

    def test_to_quadlet(self) -> None:
        unit = PodUnit(PodName="myapp", ExitPolicy="stop")
        result = unit.to_quadlet()
        assert result.startswith("[Pod]")
        assert "PodName=myapp" in result
        assert "ExitPolicy=stop" in result

    def test_with_publish_port(self) -> None:
        unit = PodUnit(PodName="myapp", PublishPort=["80:80", "443:443"])
        result = unit.to_quadlet()
        assert "PublishPort=80:80" in result
        assert "PublishPort=443:443" in result

    def test_with_network(self) -> None:
        unit = PodUnit(PodName="myapp", Network=["myapp-frontend"])
        assert unit.Network == ["myapp-frontend"]

    def test_with_dns(self) -> None:
        unit = PodUnit(PodName="myapp", DNS=["8.8.8.8"])
        result = unit.to_quadlet()
        assert "DNS=8.8.8.8" in result


# ---------------------------------------------------------------------------
# NetworkUnit
# ---------------------------------------------------------------------------


class TestNetworkUnit:
    """Tests for NetworkUnit."""

    def test_minimal(self) -> None:
        unit = NetworkUnit(NetworkName="frontend")
        assert unit.NetworkName == "frontend"

    def test_to_quadlet(self) -> None:
        unit = NetworkUnit(NetworkName="frontend", Driver="bridge")
        result = unit.to_quadlet()
        assert result.startswith("[Network]")
        assert "NetworkName=frontend" in result
        assert "Driver=bridge" in result

    def test_with_subnet(self) -> None:
        unit = NetworkUnit(
            NetworkName="frontend",
            Subnet=["172.20.0.0/16"],
        )
        result = unit.to_quadlet()
        assert "Subnet=172.20.0.0/16" in result

    def test_with_ipam_driver(self) -> None:
        unit = NetworkUnit(NetworkName="frontend", IPAMDriver="default")
        assert unit.IPAMDriver == "default"

    def test_with_ipv6(self) -> None:
        unit = NetworkUnit(NetworkName="frontend", IPv6=True)
        assert unit.IPv6 is True

    def test_with_internal(self) -> None:
        unit = NetworkUnit(NetworkName="frontend", Internal=True)
        assert unit.Internal is True

    def test_with_label(self) -> None:
        unit = NetworkUnit(NetworkName="frontend", Label=["com.example=test"])
        result = unit.to_quadlet()
        assert "Label=com.example=test" in result


# ---------------------------------------------------------------------------
# VolumeUnit
# ---------------------------------------------------------------------------


class TestVolumeUnit:
    """Tests for VolumeUnit."""

    def test_minimal(self) -> None:
        unit = VolumeUnit(VolumeName="data")
        assert unit.VolumeName == "data"

    def test_to_quadlet(self) -> None:
        unit = VolumeUnit(VolumeName="data", Driver="local")
        result = unit.to_quadlet()
        assert result.startswith("[Volume]")
        assert "VolumeName=data" in result
        assert "Driver=local" in result

    def test_with_label(self) -> None:
        unit = VolumeUnit(VolumeName="data", Label=["com.example=data"])
        result = unit.to_quadlet()
        assert "Label=com.example=data" in result

    def test_with_driver(self) -> None:
        unit = VolumeUnit(VolumeName="data", Driver="nfs")
        assert unit.Driver == "nfs"


# ---------------------------------------------------------------------------
# BuildUnit
# ---------------------------------------------------------------------------


class TestBuildUnit:
    """Tests for BuildUnit."""

    def test_minimal(self) -> None:
        unit = BuildUnit(ImageTag="myapp-web")
        assert unit.ImageTag == "myapp-web"

    def test_to_quadlet(self) -> None:
        unit = BuildUnit(ImageTag="myapp-web", SetWorkingDirectory=".")
        result = unit.to_quadlet()
        assert result.startswith("[Build]")
        assert "ImageTag=myapp-web" in result
        assert "SetWorkingDirectory=." in result

    def test_with_file(self) -> None:
        unit = BuildUnit(ImageTag="myapp-web", File="Dockerfile.custom")
        assert unit.File == "Dockerfile.custom"

    def test_with_target(self) -> None:
        unit = BuildUnit(ImageTag="myapp-web", Target="production")
        assert unit.Target == "production"

    def test_with_pull(self) -> None:
        unit = BuildUnit(ImageTag="myapp-web", Pull="always")
        assert unit.Pull == "always"

    def test_with_network(self) -> None:
        unit = BuildUnit(ImageTag="myapp-web", Network="host")
        assert unit.Network == "host"

    def test_with_label(self) -> None:
        unit = BuildUnit(ImageTag="myapp-web", Label=["version=1.0"])
        result = unit.to_quadlet()
        assert "Label=version=1.0" in result

    def test_with_secret(self) -> None:
        unit = BuildUnit(ImageTag="myapp-web", Secret=["mysecret"])
        assert unit.Secret == ["mysecret"]

    def test_with_environment(self) -> None:
        unit = BuildUnit(ImageTag="myapp-web", Environment=["FOO=bar"])
        assert unit.Environment == ["FOO=bar"]
