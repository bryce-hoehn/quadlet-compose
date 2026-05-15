"""Tests for utils/converters/service.py."""

import pytest

from utils.converters.service import (
    convert_cap_add,
    convert_cap_drop,
    convert_cgroup,
    convert_command,
    convert_container_name,
    convert_devices,
    convert_dns,
    convert_dns_search,
    convert_entrypoint,
    convert_environment,
    convert_expose,
    convert_extra_hosts,
    convert_group_add,
    convert_healthcheck,
    convert_hostname,
    convert_image,
    convert_init,
    convert_logging,
    convert_mem_limit,
    convert_networks,
    convert_pids_limit,
    convert_ports,
    convert_pull_policy,
    convert_read_only,
    convert_secrets,
    convert_shm_size,
    convert_stop_grace_period,
    convert_stop_signal,
    convert_tmpfs,
    convert_ulimits,
    convert_user,
    convert_volumes,
    convert_working_dir,
)

# ---------------------------------------------------------------------------
# Simple scalar converters
# ---------------------------------------------------------------------------


class TestConvertImage:
    def test_none(self) -> None:
        assert convert_image(None) == {}

    def test_string(self) -> None:
        assert convert_image("nginx:latest") == {"Image": "nginx:latest"}


class TestConvertContainerName:
    def test_none(self) -> None:
        assert convert_container_name(None) == {}

    def test_string(self) -> None:
        assert convert_container_name("my-container") == {
            "ContainerName": "my-container"
        }


class TestConvertHostname:
    def test_none(self) -> None:
        assert convert_hostname(None) == {}

    def test_string(self) -> None:
        assert convert_hostname("webhost") == {"HostName": "webhost"}


class TestConvertWorkingDir:
    def test_none(self) -> None:
        assert convert_working_dir(None) == {}

    def test_string(self) -> None:
        assert convert_working_dir("/app") == {"WorkingDir": "/app"}


class TestConvertUser:
    def test_none(self) -> None:
        assert convert_user(None) == {}

    def test_string(self) -> None:
        assert convert_user("appuser") == {"User": "appuser"}


class TestConvertInit:
    def test_none(self) -> None:
        assert convert_init(None) == {}

    def test_false(self) -> None:
        assert convert_init(False) == {}

    def test_true(self) -> None:
        assert convert_init(True) == {"Init": "true"}


class TestConvertReadOnly:
    def test_none(self) -> None:
        assert convert_read_only(None) == {}

    def test_false(self) -> None:
        assert convert_read_only(False) == {}

    def test_true(self) -> None:
        assert convert_read_only(True) == {"ReadOnly": "true"}


class TestConvertCgroup:
    def test_none(self) -> None:
        assert convert_cgroup(None) == {}

    def test_value(self) -> None:
        assert convert_cgroup("private") == {"Cgroups": "private"}


class TestConvertPullPolicy:
    def test_none(self) -> None:
        assert convert_pull_policy(None) == {}

    def test_value(self) -> None:
        assert convert_pull_policy("always") == {"PullPolicy": "always"}


class TestConvertStopSignal:
    def test_none(self) -> None:
        assert convert_stop_signal(None) == {}

    def test_value(self) -> None:
        assert convert_stop_signal("SIGTERM") == {"StopSignal": "SIGTERM"}


class TestConvertStopGracePeriod:
    def test_none(self) -> None:
        assert convert_stop_grace_period(None) == {}

    def test_string_duration(self) -> None:
        assert convert_stop_grace_period("30s") == {"StopTimeout": "30"}

    def test_int(self) -> None:
        assert convert_stop_grace_period(30) == {"StopTimeout": "30"}

    def test_go_duration(self) -> None:
        assert convert_stop_grace_period("1m30s") == {"StopTimeout": "90"}


class TestConvertShmSize:
    def test_none(self) -> None:
        assert convert_shm_size(None) == {}

    def test_value(self) -> None:
        assert convert_shm_size("64m") == {"ShmemSize": "64m"}


class TestConvertMemLimit:
    def test_none(self) -> None:
        assert convert_mem_limit(None) == {}

    def test_value(self) -> None:
        assert convert_mem_limit("512m") == {"Memory": "512m"}


class TestConvertPidsLimit:
    def test_none(self) -> None:
        assert convert_pids_limit(None) == {}

    def test_value(self) -> None:
        assert convert_pids_limit(100) == {"PidsLimit": "100"}


# ---------------------------------------------------------------------------
# Command / Entrypoint
# ---------------------------------------------------------------------------


class TestConvertCommand:
    def test_none(self) -> None:
        assert convert_command(None) == {}

    def test_string(self) -> None:
        assert convert_command('nginx -g "daemon off;"') == {
            "Exec": 'nginx -g "daemon off;"'
        }

    def test_list(self) -> None:
        assert convert_command(["nginx", "-g", "daemon off;"]) == {
            "Exec": ["nginx", "-g", "daemon off;"]
        }


class TestConvertEntrypoint:
    def test_none(self) -> None:
        assert convert_entrypoint(None) == {}

    def test_string(self) -> None:
        assert convert_entrypoint("/bin/sh") == {"Entrypoint": "/bin/sh"}

    def test_list(self) -> None:
        assert convert_entrypoint(["/bin/sh", "-c"]) == {
            "Entrypoint": ["/bin/sh", "-c"]
        }


# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------


class TestConvertEnvironment:
    def test_none(self) -> None:
        assert convert_environment(None) == {}

    def test_dict(self) -> None:
        result = convert_environment({"FOO": "bar", "BAZ": "qux"})
        assert result == {"Environment": ["FOO=bar", "BAZ=qux"]}

    def test_dict_skips_none_values(self) -> None:
        result = convert_environment({"FOO": "bar", "EMPTY": None})
        assert result == {"Environment": ["FOO=bar"]}

    def test_list(self) -> None:
        result = convert_environment(["FOO=bar", "BAZ=qux"])
        assert result == {"Environment": ["FOO=bar", "BAZ=qux"]}


# ---------------------------------------------------------------------------
# Ports
# ---------------------------------------------------------------------------


class TestConvertPorts:
    def test_none(self) -> None:
        assert convert_ports(None) == {}

    def test_short_form_string(self) -> None:
        result = convert_ports(["8080:80"])
        assert result == {"PublishPort": ["8080:80"]}

    def test_multiple_short_form(self) -> None:
        result = convert_ports(["8080:80", "8443:443"])
        assert result == {"PublishPort": ["8080:80", "8443:443"]}

    def test_long_form_dict(self) -> None:
        result = convert_ports([{"target": 80, "published": 8080, "protocol": "tcp"}])
        assert result == {"PublishPort": ["8080:80/tcp"]}

    def test_long_form_with_host_ip(self) -> None:
        result = convert_ports(
            [
                {
                    "target": 80,
                    "published": 8080,
                    "protocol": "tcp",
                    "host_ip": "127.0.0.1",
                }
            ]
        )
        assert result == {"PublishPort": ["127.0.0.1:8080:80/tcp"]}

    def test_long_form_default_protocol(self) -> None:
        result = convert_ports([{"target": 80, "published": 8080}])
        assert result == {"PublishPort": ["8080:80/tcp"]}

    def test_single_string(self) -> None:
        result = convert_ports("8080:80")
        assert result == {"PublishPort": ["8080:80"]}


class TestConvertExpose:
    def test_none(self) -> None:
        assert convert_expose(None) == {}

    def test_list(self) -> None:
        result = convert_expose(["80", "443"])
        assert result == {"ExposePort": ["80", "443"]}

    def test_single_int_in_list(self) -> None:
        result = convert_expose([80])
        assert result == {"ExposePort": ["80"]}


# ---------------------------------------------------------------------------
# Volumes
# ---------------------------------------------------------------------------


class TestConvertVolumes:
    def test_none(self) -> None:
        assert convert_volumes(None) == {}

    def test_bind_mount(self) -> None:
        result = convert_volumes(
            [
                {"type": "bind", "source": "/host/path", "target": "/container/path"},
            ]
        )
        assert result == {"Bind": ["/host/path:/container/path"]}

    def test_bind_mount_read_only(self) -> None:
        result = convert_volumes(
            [
                {
                    "type": "bind",
                    "source": "/host/path",
                    "target": "/container/path",
                    "read_only": True,
                },
            ]
        )
        assert result == {"Bind": ["/host/path:/container/path:ro"]}

    def test_named_volume(self) -> None:
        result = convert_volumes(
            [
                {"type": "volume", "source": "data", "target": "/data"},
            ]
        )
        assert result == {"Volume": ["data:/data"]}

    def test_anonymous_volume(self) -> None:
        result = convert_volumes(
            [
                {"type": "volume", "target": "/data"},
            ]
        )
        assert result == {"Volume": ["/data"]}

    def test_tmpfs(self) -> None:
        result = convert_volumes(
            [
                {"type": "tmpfs", "target": "/tmp"},
            ]
        )
        assert result == {"Tmpfs": ["/tmp"]}

    def test_short_form_named_volume(self) -> None:
        result = convert_volumes(["data:/data"])
        assert result == {"Volume": ["data:/data"]}

    def test_short_form_bind_mount_relative_dot(self) -> None:
        """``./data:/app/data`` → bind mount (source starts with ``.``)."""
        result = convert_volumes(["./data:/app/data"])
        assert result == {"Bind": ["./data:/app/data"]}

    def test_short_form_bind_mount_relative_dotdot(self) -> None:
        """``../data:/app/data`` → bind mount (source starts with ``.``)."""
        result = convert_volumes(["../data:/app/data"])
        assert result == {"Bind": ["../data:/app/data"]}

    def test_short_form_bind_mount_absolute(self) -> None:
        """``/host/path:/container/path`` → bind mount (source starts with ``/``)."""
        result = convert_volumes(["/host/path:/container/path"])
        assert result == {"Bind": ["/host/path:/container/path"]}

    def test_short_form_bind_mount_home(self) -> None:
        """``~/data:/app/data`` → bind mount (source starts with ``~``)."""
        result = convert_volumes(["~/data:/app/data"])
        assert result == {"Bind": ["~/data:/app/data"]}

    def test_short_form_bind_mount_with_ro(self) -> None:
        """``/host/path:/container/path:ro`` → bind mount with mode."""
        result = convert_volumes(["/host/path:/container/path:ro"])
        assert result == {"Bind": ["/host/path:/container/path:ro"]}

    def test_short_form_bind_mount_with_rw(self) -> None:
        """``/host/path:/container/path:rw`` → bind mount with mode."""
        result = convert_volumes(["/host/path:/container/path:rw"])
        assert result == {"Bind": ["/host/path:/container/path:rw"]}

    def test_short_form_named_volume_with_ro(self) -> None:
        """``myvolume:/data:ro`` → named volume with mode."""
        result = convert_volumes(["myvolume:/data:ro"])
        assert result == {"Volume": ["myvolume:/data:ro"]}

    def test_mixed_types(self) -> None:
        result = convert_volumes(
            [
                {
                    "type": "bind",
                    "source": "/host",
                    "target": "/container",
                    "read_only": True,
                },
                {"type": "volume", "source": "data", "target": "/data"},
                {"type": "tmpfs", "target": "/tmp"},
                "short:/form",
            ]
        )
        assert result == {
            "Bind": ["/host:/container:ro"],
            "Volume": ["data:/data", "short:/form"],
            "Tmpfs": ["/tmp"],
        }

    def test_mixed_short_form(self) -> None:
        """Mix of short-form bind mounts and named volumes."""
        result = convert_volumes(
            [
                "./data:/app/data",
                "myvolume:/data",
                "/host/path:/container/path",
                "~/configs:/etc/app",
            ]
        )
        assert result == {
            "Bind": [
                "./data:/app/data",
                "/host/path:/container/path",
                "~/configs:/etc/app",
            ],
            "Volume": ["myvolume:/data"],
        }

    def test_empty_list(self) -> None:
        assert convert_volumes([]) == {}


# ---------------------------------------------------------------------------
# Tmpfs
# ---------------------------------------------------------------------------


class TestConvertTmpfs:
    def test_none(self) -> None:
        assert convert_tmpfs(None) == {}

    def test_list(self) -> None:
        result = convert_tmpfs(["/run", "/tmp"])
        assert result == {"Tmpfs": ["/run", "/tmp"]}


# ---------------------------------------------------------------------------
# Devices
# ---------------------------------------------------------------------------


class TestConvertDevices:
    def test_none(self) -> None:
        assert convert_devices(None) == {}

    def test_list(self) -> None:
        result = convert_devices(["/dev/sda:/dev/xvda"])
        assert result == {"Device": ["/dev/sda:/dev/xvda"]}


# ---------------------------------------------------------------------------
# DNS
# ---------------------------------------------------------------------------


class TestConvertDns:
    def test_none(self) -> None:
        assert convert_dns(None) == {}

    def test_list(self) -> None:
        result = convert_dns(["8.8.8.8", "8.8.4.4"])
        assert result == {"DNS": ["8.8.8.8", "8.8.4.4"]}

    def test_single_string(self) -> None:
        result = convert_dns("8.8.8.8")
        assert result == {"DNS": ["8.8.8.8"]}


class TestConvertDnsSearch:
    def test_none(self) -> None:
        assert convert_dns_search(None) == {}

    def test_list(self) -> None:
        result = convert_dns_search(["example.com"])
        assert result == {"DNSSearch": ["example.com"]}


# ---------------------------------------------------------------------------
# Extra hosts
# ---------------------------------------------------------------------------


class TestConvertExtraHosts:
    def test_none(self) -> None:
        assert convert_extra_hosts(None) == {}

    def test_list(self) -> None:
        result = convert_extra_hosts(["myhost:1.2.3.4"])
        assert result == {"AddHost": ["myhost:1.2.3.4"]}


# ---------------------------------------------------------------------------
# Capabilities
# ---------------------------------------------------------------------------


class TestConvertCapAdd:
    def test_none(self) -> None:
        assert convert_cap_add(None) == {}

    def test_list(self) -> None:
        result = convert_cap_add(["NET_ADMIN", "SYS_PTRACE"])
        assert result == {"AddCapability": ["NET_ADMIN", "SYS_PTRACE"]}


class TestConvertCapDrop:
    def test_none(self) -> None:
        assert convert_cap_drop(None) == {}

    def test_list(self) -> None:
        result = convert_cap_drop(["MKNOD"])
        assert result == {"DropCapability": ["MKNOD"]}


# ---------------------------------------------------------------------------
# Group / Secrets
# ---------------------------------------------------------------------------


class TestConvertGroupAdd:
    def test_none(self) -> None:
        assert convert_group_add(None) == {}

    def test_list(self) -> None:
        result = convert_group_add(["dialout"])
        assert result == {"GroupAdd": ["dialout"]}


class TestConvertSecrets:
    def test_none(self) -> None:
        assert convert_secrets(None) == {}

    def test_list(self) -> None:
        result = convert_secrets(["db_password"])
        assert result == {"Secret": ["db_password"]}


# ---------------------------------------------------------------------------
# Ulimits
# ---------------------------------------------------------------------------


class TestConvertUlimits:
    def test_none(self) -> None:
        assert convert_ulimits(None) == {}

    def test_dict_soft_hard(self) -> None:
        result = convert_ulimits({"nofile": {"soft": 65536, "hard": 65536}})
        assert result == {"Ulimit": ["nofile=65536:65536"]}

    def test_dict_single_value(self) -> None:
        result = convert_ulimits({"nproc": 4096})
        assert result == {"Ulimit": ["nproc=4096"]}

    def test_dict_soft_defaults_to_hard(self) -> None:
        result = convert_ulimits({"nofile": {"hard": 65536}})
        assert result == {"Ulimit": ["nofile=65536:65536"]}

    def test_dict_hard_defaults_to_soft(self) -> None:
        result = convert_ulimits({"nofile": {"soft": 65536}})
        assert result == {"Ulimit": ["nofile=65536:65536"]}

    def test_empty_dict(self) -> None:
        assert convert_ulimits({}) == {}


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------


class TestConvertLogging:
    def test_none(self) -> None:
        assert convert_logging(None) == {}

    def test_driver_only(self) -> None:
        result = convert_logging({"driver": "json-file"})
        assert result == {"LogDriver": "json-file"}

    def test_driver_and_options(self) -> None:
        result = convert_logging(
            {
                "driver": "json-file",
                "options": {"max-size": "10m", "max-file": "3"},
            }
        )
        assert result == {
            "LogDriver": "json-file",
            "LogOpt": ["max-size=10m", "max-file=3"],
        }

    def test_options_only_no_driver(self) -> None:
        result = convert_logging({"options": {"max-size": "10m"}})
        assert result == {"LogOpt": ["max-size=10m"]}

    def test_empty_dict(self) -> None:
        assert convert_logging({}) == {}


# ---------------------------------------------------------------------------
# Healthcheck
# ---------------------------------------------------------------------------


class TestConvertHealthcheck:
    def test_none(self) -> None:
        assert convert_healthcheck(None) == {}

    def test_full_healthcheck(self) -> None:
        result = convert_healthcheck(
            {
                "test": ["CMD", "curl", "-f", "http://localhost/"],
                "interval": "30s",
                "timeout": "10s",
                "retries": 3,
                "start_period": "40s",
            }
        )
        assert result == {
            "HealthCmd": "curl -f http://localhost/",
            "HealthInterval": "30s",
            "HealthTimeout": "10s",
            "HealthRetries": "3",
            "HealthStartPeriod": "40s",
        }

    def test_cmd_shell_prefix_stripped(self) -> None:
        result = convert_healthcheck(
            {
                "test": ["CMD-SHELL", "curl -f http://localhost/ || exit 1"],
            }
        )
        assert result == {"HealthCmd": "'curl -f http://localhost/ || exit 1'"}

    def test_list_without_prefix(self) -> None:
        result = convert_healthcheck(
            {
                "test": ["curl", "-f", "http://localhost/"],
            }
        )
        assert result == {"HealthCmd": "curl -f http://localhost/"}

    def test_string_test(self) -> None:
        result = convert_healthcheck({"test": "curl -f http://localhost/"})
        assert result == {"HealthCmd": "curl -f http://localhost/"}

    def test_disable(self) -> None:
        result = convert_healthcheck({"disable": True})
        assert result == {"HealthCmd": "none"}

    def test_disable_overrides_test(self) -> None:
        result = convert_healthcheck(
            {
                "test": ["CMD", "true"],
                "disable": True,
            }
        )
        assert result == {"HealthCmd": "none"}

    def test_go_duration_intervals(self) -> None:
        result = convert_healthcheck(
            {
                "test": ["CMD", "true"],
                "interval": "1m30s",
                "timeout": "30s",
            }
        )
        assert result["HealthInterval"] == "90s"
        assert result["HealthTimeout"] == "30s"

    def test_empty_list_test(self) -> None:
        """CMD-SHELL with no args after prefix."""
        result = convert_healthcheck(
            {
                "test": ["CMD-SHELL"],
            }
        )
        assert result == {"HealthCmd": ""}

    def test_retries_zero(self) -> None:
        result = convert_healthcheck(
            {
                "test": ["CMD", "true"],
                "retries": 0,
            }
        )
        assert result["HealthRetries"] == "0"

    def test_cmd_with_spaces_in_arg(self) -> None:
        """Args containing spaces should be properly quoted via shlex.quote()."""
        result = convert_healthcheck(
            {
                "test": ["CMD", "curl", "-f", "http://localhost/hello world"],
            }
        )
        assert result == {"HealthCmd": "curl -f 'http://localhost/hello world'"}

    def test_cmd_with_special_chars_in_arg(self) -> None:
        """Args with shell-special characters should be quoted."""
        result = convert_healthcheck(
            {
                "test": ["CMD", "echo", "hello && rm -rf /"],
            }
        )
        assert result == {"HealthCmd": "echo 'hello && rm -rf /'"}

    def test_list_without_prefix_with_spaces(self) -> None:
        """List without CMD/CMD-SHELL prefix should also quote args with spaces."""
        result = convert_healthcheck(
            {
                "test": ["curl", "-f", "http://localhost/hello world"],
            }
        )
        assert result == {"HealthCmd": "curl -f 'http://localhost/hello world'"}

    def test_cmd_no_spaces_unchanged(self) -> None:
        """Args without spaces should not be quoted."""
        result = convert_healthcheck(
            {
                "test": ["CMD", "curl", "-f", "http://localhost/"],
            }
        )
        assert result == {"HealthCmd": "curl -f http://localhost/"}


# ---------------------------------------------------------------------------
# Networks
# ---------------------------------------------------------------------------


class TestConvertNetworks:
    def test_none(self) -> None:
        assert convert_networks(None) == {}

    def test_list(self) -> None:
        result = convert_networks(['frontend', 'backend'])
        assert result == {'Network': ['frontend', 'backend']}

    def test_dict_with_none_values(self) -> None:
        result = convert_networks({'frontend': None, 'backend': None})
        assert result == {'Network': ['frontend', 'backend']}

    def test_dict_with_aliases(self) -> None:
        result = convert_networks({
            'frontend': None,
            'backend': {'aliases': ['web']},
        })
        assert result == {
            'Network': ['frontend', 'backend'],
            'NetworkAlias': ['web'],
        }

    def test_dict_with_ipv4_address(self) -> None:
        result = convert_networks({
            'frontend': {'ipv4_address': '172.20.0.10'},
        })
        assert result == {
            'Network': ['frontend'],
            'IP': '172.20.0.10',
        }

    def test_dict_with_ipv6_address(self) -> None:
        result = convert_networks({
            'frontend': {'ipv6_address': 'fe80::1'},
        })
        assert result == {
            'Network': ['frontend'],
            'IP6': 'fe80::1',
        }

    def test_dict_with_mac_address(self) -> None:
        result = convert_networks({
            'frontend': {'mac_address': '02:42:ac:11:00:01'},
        })
        assert result == {
            'Network': ['frontend'],
            'PodmanArgs': ['--mac-address=02:42:ac:11:00:01'],
        }

    def test_dict_with_multiple_config_options(self) -> None:
        result = convert_networks({
            'frontend': {
                'aliases': ['web', 'app'],
                'ipv4_address': '172.20.0.10',
                'ipv6_address': 'fe80::1',
                'mac_address': '02:42:ac:11:00:01',
            },
        })
        assert result == {
            'Network': ['frontend'],
            'NetworkAlias': ['web', 'app'],
            'IP': '172.20.0.10',
            'IP6': 'fe80::1',
            'PodmanArgs': ['--mac-address=02:42:ac:11:00:01'],
        }

    def test_dict_multiple_networks_with_config(self) -> None:
        """Last network wins for IP fields; aliases are accumulated."""
        result = convert_networks({
            'frontend': {'ipv4_address': '172.20.0.10', 'aliases': ['web']},
            'backend': {'ipv4_address': '172.21.0.20', 'aliases': ['api']},
        })
        assert result == {
            'Network': ['frontend', 'backend'],
            'NetworkAlias': ['web', 'api'],
            'IP': '172.21.0.20',
        }

    def test_dict_unsupported_fields_dropped(self) -> None:
        """``link_local_ips``, ``priority``, ``driver_opts`` are silently dropped."""
        result = convert_networks({
            'frontend': {
                'link_local_ips': ['169.254.0.1'],
                'priority': 100,
                'driver_opts': {'com.docker.some': 'value'},
            },
        })
        assert result == {'Network': ['frontend']}

    def test_empty_list(self) -> None:
        assert convert_networks([]) == {}

    def test_empty_dict(self) -> None:
        assert convert_networks({}) == {}
