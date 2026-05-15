"""Tests for utils/converters/network.py."""

from utils.converters.network import (
    convert_network_driver_opts,
    convert_network_enable_ipv6,
    convert_network_internal,
    convert_network_ipam,
    convert_network_labels,
    convert_network_name,
)


class TestConvertNetworkName:
    def test_none(self) -> None:
        assert convert_network_name(None) == {}

    def test_string(self) -> None:
        assert convert_network_name("my-network") == {"NetworkName": "my-network"}


class TestConvertNetworkDriverOpts:
    def test_none(self) -> None:
        assert convert_network_driver_opts(None) == {}

    def test_dict(self) -> None:
        result = convert_network_driver_opts({"com.docker.network.driver.mtu": "1500"})
        assert result == {"Options": ["com.docker.network.driver.mtu=1500"]}

    def test_non_dict(self) -> None:
        assert convert_network_driver_opts("string") == {}


class TestConvertNetworkInternal:
    def test_none(self) -> None:
        assert convert_network_internal(None) == {}

    def test_false(self) -> None:
        assert convert_network_internal(False) == {}

    def test_true(self) -> None:
        assert convert_network_internal(True) == {"Internal": "true"}


class TestConvertNetworkEnableIpv6:
    def test_none(self) -> None:
        assert convert_network_enable_ipv6(None) == {}

    def test_false(self) -> None:
        assert convert_network_enable_ipv6(False) == {}

    def test_true(self) -> None:
        assert convert_network_enable_ipv6(True) == {"IPv6": "true"}


class TestConvertNetworkLabels:
    def test_none(self) -> None:
        assert convert_network_labels(None) == {}

    def test_dict(self) -> None:
        result = convert_network_labels({"app": "web", "env": "prod"})
        assert result == {"Label": ["app=web", "env=prod"]}

    def test_list(self) -> None:
        result = convert_network_labels(["app=web"])
        assert result == {"Label": ["app=web"]}

    def test_unknown_type(self) -> None:
        assert convert_network_labels(42) == {}


class TestConvertNetworkIpam:
    def test_none(self) -> None:
        assert convert_network_ipam(None) == {}

    def test_driver_only(self) -> None:
        result = convert_network_ipam({"driver": "default"})
        assert result == {"IPAMDriver": "default"}

    def test_config_with_subnet_and_gateway(self) -> None:
        result = convert_network_ipam(
            {
                "driver": "default",
                "config": [
                    {"subnet": "172.20.0.0/16", "gateway": "172.20.0.1"},
                ],
            }
        )
        assert result == {
            "IPAMDriver": "default",
            "Subnet": ["172.20.0.0/16"],
            "Gateway": ["172.20.0.1"],
        }

    def test_config_subnet_only(self) -> None:
        result = convert_network_ipam(
            {
                "config": [{"subnet": "172.20.0.0/16"}],
            }
        )
        assert result == {"Subnet": ["172.20.0.0/16"]}

    def test_config_gateway_only(self) -> None:
        result = convert_network_ipam(
            {
                "config": [{"gateway": "172.20.0.1"}],
            }
        )
        assert result == {"Gateway": ["172.20.0.1"]}

    def test_multiple_configs(self) -> None:
        result = convert_network_ipam(
            {
                "config": [
                    {"subnet": "172.20.0.0/16"},
                    {"subnet": "172.21.0.0/16"},
                ],
            }
        )
        assert result == {
            "Subnet": ["172.20.0.0/16", "172.21.0.0/16"],
        }

    def test_empty_config_list(self) -> None:
        result = convert_network_ipam({"config": []})
        assert result == {}

    def test_empty_dict(self) -> None:
        assert convert_network_ipam({}) == {}
