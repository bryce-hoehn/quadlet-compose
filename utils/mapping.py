"""Compose-spec → Quadlet unit mapping layer.

Provides declarative field maps and converter functions to translate
compose-spec Pydantic models into Podman Quadlet unit models.

Three mapping patterns are supported:
  1:1 rename       — compose field → quadlet field (same type)
  1:1 + conversion — compose field → quadlet field (type transform)
  1:N expansion    — compose field → multiple quadlet fields (e.g. healthcheck)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, TypeVar

from compose_spec.models import (
    Healthcheck,
    Network,
    Service,
    ServiceBuild,
    ServiceLogging,
    ServicePorts,
    ServiceVolumes,
    ServiceVolumesType,
    Volume,
)
from pydantic import BaseModel

from quadlet_types.build import BuildUnit
from quadlet_types.container import ContainerUnit
from quadlet_types.network import NetworkUnit
from quadlet_types.pod import PodUnit
from quadlet_types.volume import VolumeUnit

# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

#: A converter maps a raw compose value to a dict of {quadlet_field: value}.
#: For 1:1 mappings the dict has one entry; for 1:N it has several.
Converter = Callable[[Any], dict[str, Any]]

#: A field-map entry: (compose_attr, quadlet_attr, converter | None)
FieldMapEntry = tuple[str, str, Converter | None]

T = TypeVar("T", bound=BaseModel)

# ---------------------------------------------------------------------------
# Converter helpers
# ---------------------------------------------------------------------------


def _as_list(val: Any) -> list[str]:
    """Coerce a value to ``list[str]``."""
    if val is None:
        return []
    if isinstance(val, list):
        return val
    if isinstance(val, (set, frozenset)):
        return sorted(val)
    return [str(val)]


def _as_optional_list(val: Any) -> list[str] | None:
    """Coerce to ``list[str] | None``, returning None for empty/null."""
    result = _as_list(val)
    return result if result else None


def convert_list_or_dict_to_env(val: Any) -> dict[str, Any]:
    """Convert ``ListOrDict`` (environment) to ``Environment: list[str]``.

    Compose env can be a dict ``{KEY: VAL}`` or a list ``["KEY=VAL"]``.
    Quadlet expects ``Environment=["KEY=VAL", ...]``.
    """
    if val is None:
        return {}
    if isinstance(val, list):
        return {"Environment": [str(v) for v in val]}
    if isinstance(val, dict):
        pairs: list[str] = []
        for k, v in val.items():
            if v is None:
                pairs.append(str(k))
            else:
                pairs.append(f"{k}={v}")
        return {"Environment": pairs}
    return {"Environment": [str(val)]}


def convert_list_or_dict_to_kv(val: Any, field_name: str) -> dict[str, Any]:
    """Convert ``ListOrDict`` to ``list[str]`` of ``KEY=VALUE`` pairs."""
    if val is None:
        return {}
    if isinstance(val, list):
        return {field_name: [str(v) for v in val]}
    if isinstance(val, dict):
        pairs: list[str] = []
        for k, v in val.items():
            pairs.append(f"{k}={v}")
        return {field_name: pairs}
    return {}


def convert_list_or_dict_to_labels(val: Any) -> dict[str, Any]:
    """Convert ``ListOrDict`` (labels) to ``Label: list[str]``."""
    return convert_list_or_dict_to_kv(val, "Label")


def convert_list_or_dict_to_sysctls(val: Any) -> dict[str, Any]:
    """Convert ``ListOrDict`` (sysctls) to ``Sysctl: list[str]``."""
    return convert_list_or_dict_to_kv(val, "Sysctl")


def convert_list_or_dict_to_build_env(val: Any) -> dict[str, Any]:
    """Convert ``ListOrDict`` (build args) to ``Environment: list[str]``."""
    return convert_list_or_dict_to_kv(val, "Environment")


def convert_list_or_dict_to_build_labels(val: Any) -> dict[str, Any]:
    """Convert ``ListOrDict`` (build labels) to ``Label: list[str]``."""
    return convert_list_or_dict_to_kv(val, "Label")


def convert_ports(val: Any) -> dict[str, Any]:
    """Convert compose ``ports`` to ``PublishPort: list[str]``.

    Handles short-form strings (``"8080:80"``), floats, and long-form
    ``ServicePorts`` objects.
    """
    if val is None:
        return {}
    result: list[str] = []
    for port in val:
        if isinstance(port, (int, float)):
            result.append(str(int(port)))
        elif isinstance(port, str):
            result.append(port)
        elif isinstance(port, ServicePorts):
            parts: list[str] = []
            host_ip = port.host_ip
            published = port.published
            target = port.target
            protocol = port.protocol

            if host_ip:
                parts.append(str(host_ip))
            if published is not None:
                parts.append(str(published))
            if target is not None:
                if parts:
                    parts.append(f":{target}")
                else:
                    parts.append(str(target))
            port_str = (
                ":".join(
                    str(published) if published else "",
                    str(target) if target else "",
                )
                if not host_ip and published and target
                else "".join(parts)
            )

            # Simpler approach: build ip:hostPort:containerPort[/proto]
            segments: list[str] = []
            if host_ip:
                segments.append(host_ip)
            if published is not None:
                segments.append(str(published))
            if target is not None:
                segments.append(str(target))
            port_str = ":".join(segments)
            if protocol:
                port_str = f"{port_str}/{protocol}"
            result.append(port_str)
        else:
            result.append(str(port))
    return {"PublishPort": result} if result else {}


def convert_expose(val: Any) -> dict[str, Any]:
    """Convert compose ``expose`` to ``ExposeHostPort: list[str]``."""
    if val is None:
        return {}
    result = [str(int(p)) if isinstance(p, float) else str(p) for p in val]
    return {"ExposeHostPort": result} if result else {}


def convert_volumes(val: Any) -> dict[str, Any]:
    """Convert compose ``volumes`` to ``Volume: list[str]`` and ``Tmpfs: list[str]``.

    Handles short-form strings (``"host:/container:mode"``) and long-form
    ``ServiceVolumes`` objects.
    """
    if val is None:
        return {}
    volumes: list[str] = []
    tmpfs: list[str] = []
    for vol in val:
        if isinstance(vol, str):
            volumes.append(vol)
        elif isinstance(vol, ServiceVolumes):
            if vol.type == ServiceVolumesType.tmpfs:
                # tmpfs: target only, optionally with size
                dest = vol.target or ""
                tmpfs_entry = dest
                if vol.tmpfs and vol.tmpfs.size is not None:
                    tmpfs_entry = f"{dest}:size={vol.tmpfs.size}"
                if tmpfs_entry:
                    tmpfs.append(tmpfs_entry)
            elif vol.type == ServiceVolumesType.bind:
                # bind: source:target[:options]
                parts = [vol.source or "", vol.target or ""]
                opts: list[str] = []
                if vol.read_only:
                    opts.append("ro")
                if vol.bind:
                    if vol.bind.propagation:
                        opts.append(vol.bind.propagation)
                    if vol.bind.selinux:
                        opts.append(vol.bind.selinux.value)
                if opts:
                    parts.append(",".join(opts))
                volumes.append(":".join(parts))
            elif vol.type == ServiceVolumesType.volume:
                # named volume: source:target[:options]
                parts = [vol.source or "", vol.target or ""]
                opts: list[str] = []
                if vol.read_only:
                    opts.append("ro")
                if vol.volume and vol.volume.nocopy:
                    opts.append("nocopy")
                if opts:
                    parts.append(",".join(opts))
                volumes.append(":".join(parts))
            else:
                # Fallback: source:target
                if vol.source and vol.target:
                    volumes.append(f"{vol.source}:{vol.target}")
                elif vol.target:
                    volumes.append(vol.target)
    result: dict[str, Any] = {}
    if volumes:
        result["Volume"] = volumes
    if tmpfs:
        result["Tmpfs"] = tmpfs
    return result


def convert_healthcheck(val: Any) -> dict[str, Any]:
    """Convert compose ``Healthcheck`` to multiple ``Health*`` quadlet fields.

    This is a 1:N expansion: one compose healthcheck object maps to up to
    14 quadlet fields (HealthCmd, HealthInterval, etc.).
    """
    if val is None:
        return {}
    if not isinstance(val, Healthcheck):
        return {}

    result: dict[str, Any] = {}

    if val.disable:
        # Podman uses "none" as the health-cmd to disable
        result["HealthCmd"] = "none"
        return result

    if val.test is not None:
        if isinstance(val.test, list):
            if val.test and val.test[0] in ("CMD", "CMD-SHELL"):
                cmd = val.test[0]
                args = val.test[1:]
                if cmd == "CMD-SHELL" and args:
                    # CMD-SHELL: join args into a single shell command
                    result["HealthCmd"] = " ".join(args)
                elif args:
                    # CMD: pass as-is
                    result["HealthCmd"] = " ".join(args)
                else:
                    result["HealthCmd"] = " ".join(val.test)
            else:
                result["HealthCmd"] = " ".join(val.test)
        else:
            result["HealthCmd"] = str(val.test)

    if val.interval is not None:
        result["HealthInterval"] = val.interval
    if val.timeout is not None:
        result["HealthTimeout"] = val.timeout
    if val.retries is not None:
        result["HealthRetries"] = int(val.retries)
    if val.start_period is not None:
        result["HealthStartPeriod"] = val.start_period
    if val.start_interval is not None:
        result["HealthStartupInterval"] = val.start_interval

    return result


def convert_logging(val: Any) -> dict[str, Any]:
    """Convert compose ``ServiceLogging`` to ``LogDriver`` + ``LogOpt``.

    This is a 1:N expansion: one logging object maps to two quadlet fields.
    """
    if val is None:
        return {}
    if not isinstance(val, ServiceLogging):
        return {}

    result: dict[str, Any] = {}
    if val.driver:
        result["LogDriver"] = val.driver
    if val.options:
        result["LogOpt"] = [f"{k}={v}" for k, v in val.options.items() if v is not None]
    return result


def convert_extra_hosts(val: Any) -> dict[str, Any]:
    """Convert compose ``extra_hosts`` to ``AddHost: list[str]``.

    Handles dict form ``{hostname: ip}`` and list form ``["hostname:ip"]``.
    """
    if val is None:
        return {}
    result: list[str] = []
    root = val.root if hasattr(val, "root") else val
    if isinstance(root, dict):
        for hostname, ips in root.items():
            if isinstance(ips, list):
                for ip in ips:
                    result.append(f"{hostname}:{ip}")
            else:
                result.append(f"{hostname}:{ips}")
    elif isinstance(root, (list, set)):
        for entry in root:
            result.append(str(entry))
    return {"AddHost": result} if result else {}


def convert_ulimits(val: Any) -> dict[str, Any]:
    """Convert compose ``Ulimits`` to ``Ulimit: list[str]``.

    Handles ``{name: limit}`` where limit is int, str, or ``{soft, hard}``.
    """
    if val is None:
        return {}
    root = val.root if hasattr(val, "root") else val
    if not isinstance(root, dict):
        return {}
    result: list[str] = []
    for name, limit in root.items():
        if isinstance(limit, (int, str)):
            result.append(f"{name}={limit}")
        elif isinstance(limit, dict):
            soft = limit.get("soft", limit.get(0))
            hard = limit.get("hard", limit.get(1))
            if soft is not None and hard is not None:
                result.append(f"{name}={soft}:{hard}")
            elif hard is not None:
                result.append(f"{name}={hard}")
    return {"Ulimit": result} if result else {}


def convert_tmpfs(val: Any) -> dict[str, Any]:
    """Convert compose ``tmpfs`` (StringOrList) to ``Tmpfs: list[str]``."""
    if val is None:
        return {}
    root = val.root if hasattr(val, "root") else val
    if isinstance(root, str):
        return {"Tmpfs": [root]}
    if isinstance(root, (list, set)):
        return {"Tmpfs": [str(v) for v in root]}
    return {}


def convert_dns(val: Any) -> dict[str, Any]:
    """Convert compose ``dns`` (StringOrList) to ``DNS: list[str]``."""
    if val is None:
        return {}
    root = val.root if hasattr(val, "root") else val
    if isinstance(root, str):
        return {"DNS": [root]}
    if isinstance(root, (list, set)):
        return {"DNS": [str(v) for v in root]}
    return {}


def convert_dns_search(val: Any) -> dict[str, Any]:
    """Convert compose ``dns_search`` (StringOrList) to ``DNSSearch: list[str]``."""
    if val is None:
        return {}
    root = val.root if hasattr(val, "root") else val
    if isinstance(root, str):
        return {"DNSSearch": [root]}
    if isinstance(root, (list, set)):
        return {"DNSSearch": [str(v) for v in root]}
    return {}


def convert_networks(val: Any) -> dict[str, Any]:
    """Convert compose ``networks`` to ``Network: list[str]``.

    Handles list form ``["net1", "net2"]`` and dict form
    ``{"net1": {ipv4_address: ...}, ...}``.  Also extracts ``NetworkAlias``
    from dict-form entries.
    """
    if val is None:
        return {}
    root = val.root if hasattr(val, "root") else val
    networks: list[str] = []
    aliases: list[str] = []

    if isinstance(root, (list, set)):
        networks = [str(v) for v in root]
    elif isinstance(root, dict):
        for name, config in root.items():
            networks.append(str(name))
            if (
                config is not None
                and hasattr(config, "ipv4_address")
                and config.ipv4_address
            ):
                # IP per-network is not directly supported in quadlet Network
                pass
            if config is not None and hasattr(config, "aliases") and config.aliases:
                aliases.extend(config.aliases)
    result: dict[str, Any] = {}
    if networks:
        result["Network"] = networks
    if aliases:
        result["NetworkAlias"] = aliases
    return result


def convert_secrets(val: Any) -> dict[str, Any]:
    """Convert compose ``secrets`` to ``Secret: list[str]``.

    Handles short-form strings and long-form objects with ``source``/``target``.
    """
    if val is None:
        return {}
    root = val.root if hasattr(val, "root") else val
    if not isinstance(root, list):
        return {}
    result: list[str] = []
    for entry in root:
        if isinstance(entry, str):
            result.append(entry)
        elif hasattr(entry, "source") and entry.source:
            result.append(entry.source)
    return {"Secret": result} if result else {}


def convert_group_add(val: Any) -> dict[str, Any]:
    """Convert compose ``group_add`` to ``GroupAdd: list[str]``."""
    if val is None:
        return {}
    result = [str(g) for g in val]
    return {"GroupAdd": result} if result else {}


def convert_pull_policy(val: Any) -> dict[str, Any]:
    """Convert compose ``pull_policy`` to ``Pull: str``.

    Maps ``if_not_present`` → ``missing``; others pass through.
    """
    if val is None:
        return {}
    policy = str(val)
    if policy == "if_not_present":
        policy = "missing"
    # Only return if it's a valid quadlet Pull value
    valid = ("always", "missing", "never", "newer")
    if policy in valid:
        return {"Pull": policy}
    return {}


def convert_user(val: Any) -> dict[str, Any]:
    """Convert compose ``user`` to ``User`` and optionally ``Group``.

    Compose ``user`` can be ``"user"``, ``"user:group"``, or ``"uid:gid"``.
    Quadlet has separate ``User`` and ``Group`` fields.
    """
    if val is None:
        return {}
    user_str = str(val)
    if ":" in user_str:
        user, group = user_str.split(":", 1)
        return {"User": user, "Group": group}
    return {"User": user_str}


def convert_entrypoint(val: Any) -> dict[str, Any]:
    """Convert compose ``entrypoint`` (Command) to ``Entrypoint: str``."""
    if val is None:
        return {}
    root = val.root if hasattr(val, "root") else val
    if isinstance(root, list):
        return {"Entrypoint": " ".join(root)}
    if isinstance(root, str):
        return {"Entrypoint": root}
    return {}


def convert_command(val: Any) -> dict[str, Any]:
    """Convert compose ``command`` (Command) to ``Exec: list[str]``."""
    if val is None:
        return {}
    root = val.root if hasattr(val, "root") else val
    if isinstance(root, list):
        return {"Exec": root}
    if isinstance(root, str):
        # Split on spaces for simple commands, wrap in list
        return {"Exec": [root]}
    return {}


def convert_init(val: Any) -> dict[str, Any]:
    """Convert compose ``init`` to ``RunInit: bool``."""
    if val is None:
        return {}
    return {"RunInit": bool(val)}


def convert_read_only(val: Any) -> dict[str, Any]:
    """Convert compose ``read_only`` to ``ReadOnly: bool``."""
    if val is None:
        return {}
    return {"ReadOnly": bool(val)}


def convert_stop_signal(val: Any) -> dict[str, Any]:
    """Convert compose ``stop_signal`` to ``StopSignal: str``."""
    if val is None:
        return {}
    return {"StopSignal": str(val)}


def convert_stop_grace_period(val: Any) -> dict[str, Any]:
    """Convert compose ``stop_grace_period`` to ``StopTimeout: int``.

    Parses duration strings like ``"1m30s"`` into seconds.
    """
    if val is None:
        return {}
    return {"StopTimeout": _parse_duration_seconds(val)}


def convert_pids_limit(val: Any) -> dict[str, Any]:
    """Convert compose ``pids_limit`` to ``PidsLimit: int``."""
    if val is None:
        return {}
    return {"PidsLimit": int(val)}


def convert_shm_size(val: Any) -> dict[str, Any]:
    """Convert compose ``shm_size`` to ``ShmSize: str``."""
    if val is None:
        return {}
    return {"ShmSize": str(val)}


def convert_mem_limit(val: Any) -> dict[str, Any]:
    """Convert compose ``mem_limit`` to ``Memory: str``."""
    if val is None:
        return {}
    return {"Memory": str(val)}


def convert_cgroup(val: Any) -> dict[str, Any]:
    """Convert compose ``cgroup`` to ``CgroupsMode: str``."""
    if val is None:
        return {}
    root = val.root if hasattr(val, "root") else val
    root = str(root)
    if root == "private":
        return {"CgroupsMode": "enabled"}
    if root == "host":
        return {"CgroupsMode": "disabled"}
    return {}


def convert_devices(val: Any) -> dict[str, Any]:
    """Convert compose ``devices`` to ``AddDevice: list[str]``."""
    if val is None:
        return {}
    result: list[str] = []
    for dev in val:
        if isinstance(dev, str):
            result.append(dev)
        elif hasattr(dev, "source"):
            source = dev.source or ""
            target = dev.target if hasattr(dev, "target") and dev.target else source
            result.append(f"{source}:{target}")
    return {"AddDevice": result} if result else {}


def convert_hostname(val: Any) -> dict[str, Any]:
    """Convert compose ``hostname`` to ``HostName: str``."""
    if val is None:
        return {}
    return {"HostName": str(val)}


def convert_working_dir(val: Any) -> dict[str, Any]:
    """Convert compose ``working_dir`` to ``WorkingDir: str``."""
    if val is None:
        return {}
    return {"WorkingDir": str(val)}


def convert_container_name(val: Any) -> dict[str, Any]:
    """Convert compose ``container_name`` to ``ContainerName: str``."""
    if val is None:
        return {}
    return {"ContainerName": str(val)}


def convert_image(val: Any) -> dict[str, Any]:
    """Convert compose ``image`` to ``Image: str``."""
    if val is None:
        return {}
    return {"Image": str(val)}


def convert_cap_add(val: Any) -> dict[str, Any]:
    """Convert compose ``cap_add`` to ``AddCapability: list[str]``."""
    if val is None:
        return {}
    return {"AddCapability": sorted(val)}


def convert_cap_drop(val: Any) -> dict[str, Any]:
    """Convert compose ``cap_drop`` to ``DropCapability: list[str]``."""
    if val is None:
        return {}
    return {"DropCapability": sorted(val)}


# ---------------------------------------------------------------------------
# Build-specific converters
# ---------------------------------------------------------------------------


def convert_build_context(val: Any) -> dict[str, Any]:
    """Convert compose build ``context`` to ``SetWorkingDirectory: str``."""
    if val is None:
        return {}
    return {"SetWorkingDirectory": str(val)}


def convert_build_dockerfile(val: Any) -> dict[str, Any]:
    """Convert compose build ``dockerfile`` to ``File: str``."""
    if val is None:
        return {}
    return {"File": str(val)}


def convert_build_target(val: Any) -> dict[str, Any]:
    """Convert compose build ``target`` to ``Target: str``."""
    if val is None:
        return {}
    return {"Target": str(val)}


def convert_build_pull(val: Any) -> dict[str, Any]:
    """Convert compose build ``pull`` to ``Pull: str``."""
    if val is None:
        return {}
    pull_val = str(val).lower()
    if pull_val in ("true", "always"):
        return {"Pull": "always"}
    if pull_val in ("false", "never"):
        return {"Pull": "never"}
    if pull_val == "missing":
        return {"Pull": "missing"}
    return {"Pull": "newer"}


def convert_build_network(val: Any) -> dict[str, Any]:
    """Convert compose build ``network`` to ``Network: str``."""
    if val is None:
        return {}
    return {"Network": str(val)}


def convert_build_secrets(val: Any) -> dict[str, Any]:
    """Convert compose build ``secrets`` to ``Secret: list[str]``."""
    return convert_secrets(val)


def convert_build_labels(val: Any) -> dict[str, Any]:
    """Convert compose build ``labels`` to ``Label: list[str]``."""
    return convert_list_or_dict_to_build_labels(val)


# ---------------------------------------------------------------------------
# Network-specific converters
# ---------------------------------------------------------------------------


def convert_network_driver_opts(val: Any) -> dict[str, Any]:
    """Convert compose network ``driver_opts`` to ``Options: str``."""
    if val is None:
        return {}
    if isinstance(val, dict):
        opts = ",".join(f"{k}={v}" for k, v in val.items())
        return {"Options": opts}
    return {}


def convert_network_ipam(val: Any) -> dict[str, Any]:
    """Convert compose network ``ipam`` to quadlet IPAM fields."""
    if val is None:
        return {}
    result: dict[str, Any] = {}
    if hasattr(val, "driver") and val.driver:
        result["IPAMDriver"] = val.driver
    if hasattr(val, "config") and val.config:
        subnets: list[str] = []
        gateways: list[str] = []
        ip_ranges: list[str] = []
        for item in val.config:
            if item.subnet:
                subnets.append(item.subnet)
            if item.gateway:
                gateways.append(item.gateway)
            if item.ip_range:
                ip_ranges.append(item.ip_range)
        if subnets:
            result["Subnet"] = subnets
        if gateways:
            result["Gateway"] = gateways
        if ip_ranges:
            result["IPRange"] = ip_ranges
    return result


def convert_network_labels(val: Any) -> dict[str, Any]:
    """Convert compose network ``labels`` to ``Label: list[str]``."""
    return convert_list_or_dict_to_labels(val)


def convert_network_internal(val: Any) -> dict[str, Any]:
    """Convert compose network ``internal`` to ``Internal: bool``."""
    if val is None:
        return {}
    return {"Internal": bool(val)}


def convert_network_enable_ipv6(val: Any) -> dict[str, Any]:
    """Convert compose network ``enable_ipv6`` to ``IPv6: bool``."""
    if val is None:
        return {}
    return {"IPv6": bool(val)}


def convert_network_name(val: Any) -> dict[str, Any]:
    """Convert compose network ``name`` to ``NetworkName: str``."""
    if val is None:
        return {}
    return {"NetworkName": str(val)}


# ---------------------------------------------------------------------------
# Volume-specific converters
# ---------------------------------------------------------------------------


def convert_volume_name(val: Any) -> dict[str, Any]:
    """Convert compose volume ``name`` to ``VolumeName: str``."""
    if val is None:
        return {}
    return {"VolumeName": str(val)}


def convert_volume_labels(val: Any) -> dict[str, Any]:
    """Convert compose volume ``labels`` to ``Label: list[str]``."""
    return convert_list_or_dict_to_labels(val)


# ---------------------------------------------------------------------------
# Duration parser
# ---------------------------------------------------------------------------

_DURATION_UNITS: dict[str, int] = {
    "ns": 1,
    "us": 1,
    "µs": 1,
    "ms": 1,
    "s": 1,
    "m": 60,
    "h": 3600,
    "d": 86400,
}


def _parse_duration_seconds(val: str | int | float) -> int:
    """Parse a duration string like ``"1m30s"`` into seconds.

    Falls back to ``int(val)`` for plain numeric strings.
    """
    if isinstance(val, (int, float)):
        return int(val)
    val = str(val).strip()
    try:
        return int(val)
    except ValueError:
        pass

    # Regex parse for common formats: 1h30m, 90s, 1m30s
    import re

    total = 0
    for match in re.finditer(r"(\d+(?:\.\d+)?)\s*(ns|us|µs|ms|s|m|h|d)", val):
        amount = float(match.group(1))
        unit = match.group(2)
        if unit in _DURATION_UNITS:
            if unit in ("ns", "us", "µs", "ms"):
                # Sub-second units → round to 1 second minimum
                total += max(1, int(amount * _DURATION_UNITS[unit]))
            else:
                total += int(amount * _DURATION_UNITS[unit])
    return (
        total
        if total > 0
        else int(val.rstrip("smhd")) if val.rstrip("smhd").isdigit() else 0
    )


# ---------------------------------------------------------------------------
# Field maps
# ---------------------------------------------------------------------------

#: Service → ContainerUnit field mapping table.
#: Each entry is ``(compose_attr, quadlet_attr, converter | None)``.
#: ``None`` converter means 1:1 identity (same type, just rename).
SERVICE_FIELD_MAP: list[FieldMapEntry] = [
    # -- Identity / simple renames --
    ("image", "Image", convert_image),
    ("container_name", "ContainerName", convert_container_name),
    ("hostname", "HostName", convert_hostname),
    ("working_dir", "WorkingDir", convert_working_dir),
    # -- Capabilities --
    ("cap_add", "AddCapability", convert_cap_add),
    ("cap_drop", "DropCapability", convert_cap_drop),
    # -- Devices --
    ("devices", "AddDevice", convert_devices),
    # -- DNS --
    ("dns", "DNS", convert_dns),
    ("dns_opt", "DNSOption", lambda v: {"DNSOption": _as_optional_list(v)}),
    ("dns_search", "DNSSearch", convert_dns_search),
    # -- Entrypoint / Command --
    ("entrypoint", "Entrypoint", convert_entrypoint),
    ("command", "Exec", convert_command),
    # -- Environment --
    ("environment", "Environment", convert_list_or_dict_to_env),
    # -- Ports --
    ("ports", "PublishPort", convert_ports),
    ("expose", "ExposeHostPort", convert_expose),
    # -- Labels / Annotations --
    ("labels", "Label", convert_list_or_dict_to_labels),
    ("annotations", "Annotation", lambda v: {"Annotation": _as_optional_list(v)}),
    # -- User / Group --
    ("user", "User", convert_user),
    ("group_add", "GroupAdd", convert_group_add),
    # -- Networking --
    ("extra_hosts", "AddHost", convert_extra_hosts),
    ("networks", "Network", convert_networks),
    # -- Health (1:N expansion) --
    ("healthcheck", "", convert_healthcheck),
    # -- Logging (1:N expansion) --
    ("logging", "", convert_logging),
    # -- Limits --
    ("mem_limit", "Memory", convert_mem_limit),
    ("pids_limit", "PidsLimit", convert_pids_limit),
    ("shm_size", "ShmSize", convert_shm_size),
    # -- Sysctls --
    ("sysctls", "Sysctl", convert_list_or_dict_to_sysctls),
    # -- Tmpfs --
    ("tmpfs", "Tmpfs", convert_tmpfs),
    # -- Ulimits --
    ("ulimits", "Ulimit", convert_ulimits),
    # -- Secrets --
    ("secrets", "Secret", convert_secrets),
    # -- Pull policy --
    ("pull_policy", "Pull", convert_pull_policy),
    # -- Init --
    ("init", "RunInit", convert_init),
    # -- Read-only --
    ("read_only", "ReadOnly", convert_read_only),
    # -- Stop --
    ("stop_signal", "StopSignal", convert_stop_signal),
    ("stop_grace_period", "StopTimeout", convert_stop_grace_period),
    # -- Cgroup --
    ("cgroup", "CgroupsMode", convert_cgroup),
    # -- Volumes (1:N expansion: Volume + Tmpfs) --
    ("volumes", "", convert_volumes),
]

#: ServiceBuild → BuildUnit field mapping table.
BUILD_FIELD_MAP: list[FieldMapEntry] = [
    ("context", "SetWorkingDirectory", convert_build_context),
    ("dockerfile", "File", convert_build_dockerfile),
    ("target", "Target", convert_build_target),
    ("pull", "Pull", convert_build_pull),
    ("network", "Network", convert_build_network),
    ("args", "Environment", convert_list_or_dict_to_build_env),
    ("secrets", "Secret", convert_build_secrets),
    ("labels", "Label", convert_build_labels),
]

#: Network → NetworkUnit field mapping table.
NETWORK_FIELD_MAP: list[FieldMapEntry] = [
    ("name", "NetworkName", convert_network_name),
    ("driver", "Driver", lambda v: {"Driver": str(v)} if v else {}),
    ("driver_opts", "Options", convert_network_driver_opts),
    ("ipam", "", convert_network_ipam),
    ("internal", "Internal", convert_network_internal),
    ("enable_ipv6", "IPv6", convert_network_enable_ipv6),
    ("labels", "Label", convert_network_labels),
]

#: Volume → VolumeUnit field mapping table.
VOLUME_FIELD_MAP: list[FieldMapEntry] = [
    ("name", "VolumeName", convert_volume_name),
    ("driver", "Driver", lambda v: {"Driver": str(v)} if v else {}),
    ("labels", "Label", convert_volume_labels),
]


# ---------------------------------------------------------------------------
# Generic mapper
# ---------------------------------------------------------------------------


def _apply_field_map(
    source: BaseModel,
    field_map: list[FieldMapEntry],
) -> dict[str, Any]:
    """Apply a field map to a source model and return a flat dict of quadlet kwargs.

    For each entry in the field map:
    - Get the compose attribute value from the source model
    - If the value is None, skip
    - If a converter is provided, call it to get {quadlet_field: value}
    - Otherwise, use the quadlet_attr directly with the raw value
    """
    result: dict[str, Any] = {}
    for compose_attr, quadlet_attr, converter in field_map:
        value = getattr(source, compose_attr, None)
        if value is None:
            continue

        if converter is not None:
            converted = converter(value)
            if converted:
                result.update(converted)
        elif quadlet_attr:
            # 1:1 identity rename
            result[quadlet_attr] = value
    return result


# ---------------------------------------------------------------------------
# Public mapping functions
# ---------------------------------------------------------------------------


def map_service(
    service: Service,
    *,
    service_name: str,
    project_name: str | None = None,
    pod_name: str | None = None,
) -> ContainerUnit:
    """Map a compose ``Service`` to a quadlet ``ContainerUnit``.

    Args:
        service: The compose service model.
        service_name: The service key name from compose file.
        project_name: Optional project name for container naming.
        pod_name: Optional pod name to assign the container to.

    Returns:
        A ``ContainerUnit`` populated from the compose service.
    """
    kwargs = _apply_field_map(service, SERVICE_FIELD_MAP)

    # Set Image if not already set (required field)
    if "Image" not in kwargs:
        if service.image:
            kwargs["Image"] = service.image
        elif not service.build:
            # No image and no build — this is an error in compose
            kwargs["Image"] = service_name

    # Assign to pod if provided
    if pod_name:
        kwargs["Pod"] = pod_name

    # Set container name: explicit > project-prefixed > service name
    if "ContainerName" not in kwargs:
        if project_name:
            kwargs["ContainerName"] = f"{project_name}-{service_name}"
        else:
            kwargs["ContainerName"] = service_name

    return ContainerUnit(**kwargs)


def map_build(
    build: ServiceBuild,
    *,
    service_name: str,
    project_name: str | None = None,
) -> BuildUnit:
    """Map a compose ``ServiceBuild`` to a quadlet ``BuildUnit``.

    Args:
        build: The compose build model.
        service_name: The service key name (used for default ImageTag).
        project_name: Optional project name for image tagging.

    Returns:
        A ``BuildUnit`` populated from the compose build config.
    """
    kwargs = _apply_field_map(build, BUILD_FIELD_MAP)

    # Set ImageTag if not provided
    if "ImageTag" not in kwargs:
        tag = f"{project_name}-{service_name}" if project_name else service_name
        kwargs["ImageTag"] = tag

    return BuildUnit(**kwargs)


def map_network(
    network: Network,
    *,
    network_name: str,
    project_name: str | None = None,
) -> NetworkUnit:
    """Map a compose ``Network`` to a quadlet ``NetworkUnit``.

    Args:
        network: The compose network model.
        network_name: The network key name from compose file.
        project_name: Optional project name for network naming.

    Returns:
        A ``NetworkUnit`` populated from the compose network.
    """
    kwargs = _apply_field_map(network, NETWORK_FIELD_MAP)

    # Set NetworkName if not provided
    if "NetworkName" not in kwargs:
        if project_name:
            kwargs["NetworkName"] = f"{project_name}-{network_name}"
        else:
            kwargs["NetworkName"] = network_name

    return NetworkUnit(**kwargs)


def map_volume(
    volume: Volume,
    *,
    volume_name: str,
    project_name: str | None = None,
) -> VolumeUnit:
    """Map a compose ``Volume`` to a quadlet ``VolumeUnit``.

    Args:
        volume: The compose volume model.
        volume_name: The volume key name from compose file.
        project_name: Optional project name for volume naming.

    Returns:
        A ``VolumeUnit`` populated from the compose volume.
    """
    kwargs = _apply_field_map(volume, VOLUME_FIELD_MAP)

    # Set VolumeName if not provided
    if "VolumeName" not in kwargs:
        if project_name:
            kwargs["VolumeName"] = f"{project_name}-{volume_name}"
        else:
            kwargs["VolumeName"] = volume_name

    return VolumeUnit(**kwargs)


# ---------------------------------------------------------------------------
# QuadletBundle — orchestrator output
# ---------------------------------------------------------------------------


@dataclass
class QuadletBundle:
    """Aggregation of all quadlet units produced from a single compose file.

    Attributes:
        pod: The pod unit (one per compose project).
        containers: List of container units (one per service).
        networks: List of network units.
        volumes: List of volume units.
        builds: List of build units (for services with ``build:``).
    """

    pod: PodUnit | None = None
    containers: list[ContainerUnit] = field(default_factory=list)
    networks: list[NetworkUnit] = field(default_factory=list)
    volumes: list[VolumeUnit] = field(default_factory=list)
    builds: list[BuildUnit] = field(default_factory=list)

    def to_quadlet_files(self) -> dict[str, str]:
        """Render all units to their quadlet file contents.

        Returns:
            Dict mapping ``filename`` → ``quadlet file content``.
        """
        files: dict[str, str] = {}
        if self.pod is not None:
            name = self.pod.PodName or "pod"
            files[f"{name}.pod"] = self.pod.to_quadlet()
        for unit in self.containers:
            name = unit.ContainerName or "container"
            files[f"{name}.container"] = unit.to_quadlet()
        for unit in self.networks:
            name = unit.NetworkName or "network"
            files[f"{name}.network"] = unit.to_quadlet()
        for unit in self.volumes:
            name = unit.VolumeName or "volume"
            files[f"{name}.volume"] = unit.to_quadlet()
        for unit in self.builds:
            tag = unit.ImageTag or "build"
            files[f"{tag}.build"] = unit.to_quadlet()
        return files


def map_compose(
    compose_data: dict[str, Any],
    *,
    project_name: str | None = None,
) -> QuadletBundle:
    """Map a full compose specification dict to a ``QuadletBundle``.

    This is the top-level entry point for compose→quadlet translation.

    Args:
        compose_data: The parsed compose file as a dict (from YAML).
        project_name: Optional project name (defaults to directory name).

    Returns:
        A ``QuadletBundle`` containing all generated quadlet units.
    """
    from compose_spec.models import ComposeSpecification

    spec = ComposeSpecification.model_validate(compose_data)
    bundle = QuadletBundle()

    # Determine project name
    if not project_name:
        project_name = spec.name if spec.name else "default"

    # Create pod for the project
    bundle.pod = PodUnit(
        PodName=project_name,
        ExitPolicy="stop",
    )
    pod_name = f"{project_name}-pod"

    # Map services
    if spec.services:
        for svc_name, svc in spec.services.items():
            svc_model = Service.model_validate(svc) if isinstance(svc, dict) else svc

            # Handle build config
            if svc_model.build:
                build_obj = svc_model.build
                if isinstance(build_obj, str):
                    build_obj = ServiceBuild(context=build_obj)
                build_unit = map_build(
                    build_obj,
                    service_name=svc_name,
                    project_name=project_name,
                )
                bundle.builds.append(build_unit)

            # Map the service to a container
            container = map_service(
                svc_model,
                service_name=svc_name,
                project_name=project_name,
                pod_name=pod_name,
            )
            bundle.containers.append(container)

    # Map networks
    if spec.networks:
        for net_name, net in spec.networks.items():
            net_model = Network.model_validate(net) if isinstance(net, dict) else net
            # Skip external networks
            if net_model.external:
                continue
            network_unit = map_network(
                net_model,
                network_name=net_name,
                project_name=project_name,
            )
            bundle.networks.append(network_unit)

    # Map volumes
    if spec.volumes:
        for vol_name, vol in spec.volumes.items():
            vol_model = Volume.model_validate(vol) if isinstance(vol, dict) else vol
            # Skip external volumes
            if vol_model.external:
                continue
            volume_unit = map_volume(
                vol_model,
                volume_name=vol_name,
                project_name=project_name,
            )
            bundle.volumes.append(volume_unit)

    return bundle
