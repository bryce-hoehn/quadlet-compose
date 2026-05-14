"""Converter functions for compose Service → Quadlet ContainerUnit fields."""

from __future__ import annotations

from typing import Any

from converters._helpers import _as_list, _as_optional_list
from converters._duration import _parse_duration_seconds


def convert_command(value: Any) -> dict[str, Any]:
    """Convert compose ``command`` to ``Exec``."""
    if value is None:
        return {}
    if isinstance(value, str):
        return {"Exec": value}
    return {"Exec": _as_list(value)}


def convert_container_name(value: Any) -> dict[str, Any]:
    """Convert compose ``container_name`` to ``ContainerName``."""
    if value is None:
        return {}
    return {"ContainerName": str(value)}


def convert_entrypoint(value: Any) -> dict[str, Any]:
    """Convert compose ``entrypoint`` to ``Entrypoint``."""
    if value is None:
        return {}
    if isinstance(value, str):
        return {"Entrypoint": value}
    return {"Entrypoint": _as_list(value)}


def convert_environment(value: Any) -> dict[str, Any]:
    """Convert compose ``environment`` to ``Environment`` lines."""
    if value is None:
        return {}
    if isinstance(value, dict):
        return {"Environment": [f"{k}={v}" for k, v in value.items() if v is not None]}
    if isinstance(value, list):
        return {"Environment": [str(v) for v in value]}
    return {}


def convert_image(value: Any) -> dict[str, Any]:
    """Convert compose ``image`` to ``Image``."""
    if value is None:
        return {}
    return {"Image": str(value)}


def convert_working_dir(value: Any) -> dict[str, Any]:
    """Convert compose ``working_dir`` to ``WorkingDir``."""
    if value is None:
        return {}
    return {"WorkingDir": str(value)}


def convert_user(value: Any) -> dict[str, Any]:
    """Convert compose ``user`` to ``User``."""
    if value is None:
        return {}
    return {"User": str(value)}


def convert_hostname(value: Any) -> dict[str, Any]:
    """Convert compose ``hostname`` to ``HostName``."""
    if value is None:
        return {}
    return {"HostName": str(value)}


def convert_init(value: Any) -> dict[str, Any]:
    """Convert compose ``init`` to ``Init``."""
    if value is None or value is False:
        return {}
    return {"Init": "true"}


def convert_read_only(value: Any) -> dict[str, Any]:
    """Convert compose ``read_only`` to ``ReadOnly``."""
    if value is None or value is False:
        return {}
    return {"ReadOnly": "true"}


def convert_cgroup(value: Any) -> dict[str, Any]:
    """Convert compose ``cgroup`` to ``Cgroups``."""
    if value is None:
        return {}
    return {"Cgroups": str(value)}


def convert_pull_policy(value: Any) -> dict[str, Any]:
    """Convert compose ``pull_policy`` to ``PullPolicy``."""
    if value is None:
        return {}
    return {"PullPolicy": str(value)}


def convert_stop_signal(value: Any) -> dict[str, Any]:
    """Convert compose ``stop_signal`` to ``StopSignal``."""
    if value is None:
        return {}
    return {"StopSignal": str(value)}


def convert_stop_grace_period(value: Any) -> dict[str, Any]:
    """Convert compose ``stop_grace_period`` to ``StopTimeout`` (seconds).

    BUG FIX: Previous version multiplied by 1e9 (nanoseconds).
    """
    if value is None:
        return {}
    return {"StopTimeout": str(_parse_duration_seconds(value))}


def convert_shm_size(value: Any) -> dict[str, Any]:
    """Convert compose ``shm_size`` to ``ShmemSize``."""
    if value is None:
        return {}
    return {"ShmemSize": str(value)}


def convert_mem_limit(value: Any) -> dict[str, Any]:
    """Convert compose ``mem_limit`` to ``Memory``."""
    if value is None:
        return {}
    return {"Memory": str(value)}


def convert_pids_limit(value: Any) -> dict[str, Any]:
    """Convert compose ``pids_limit`` to ``PidsLimit``."""
    if value is None:
        return {}
    return {"PidsLimit": str(value)}


def convert_ports(value: Any) -> dict[str, Any]:
    """Convert compose ``ports`` to ``PublishPort`` lines.

    Handles short-form strings (``"8080:80"``) and long-form dicts
    (``{target: 80, published: 8080, protocol: tcp}``).
    """
    if value is None:
        return {}
    ports: list[str] = []
    for entry in _as_list(value):
        if isinstance(entry, dict):
            target = entry.get("target")
            published = entry.get("published", "")
            protocol = entry.get("protocol", "tcp")
            ip = entry.get("host_ip")
            if ip:
                ports.append(f"{ip}:{published}:{target}/{protocol}")
            else:
                ports.append(f"{published}:{target}/{protocol}")
        else:
            ports.append(str(entry))
    return {"PublishPort": ports}


def convert_expose(value: Any) -> dict[str, Any]:
    """Convert compose ``expose`` to ``ExposePort`` lines."""
    if value is None:
        return {}
    return {"ExposePort": [str(v) for v in _as_list(value)]}


def convert_volumes(value: Any) -> dict[str, Any]:
    """Convert compose ``volumes`` to ``Volume`` / ``Bind`` / ``Tmpfs`` lines."""
    if value is None:
        return {}
    volumes: list[str] = []
    binds: list[str] = []
    tmpfs_list: list[str] = []
    for entry in _as_list(value):
        if isinstance(entry, dict):
            vtype = entry.get("type", "bind")
            source = entry.get("source", "")
            target = entry.get("target", "")
            if vtype == "volume":
                volumes.append(f"{source}:{target}" if source else target)
            elif vtype == "bind":
                opts = []
                if entry.get("read_only"):
                    opts.append("ro")
                bind_str = f"{source}:{target}"
                if opts:
                    bind_str += ":" + ",".join(opts)
                binds.append(bind_str)
            elif vtype == "tmpfs":
                tmpfs_list.append(target)
        else:
            # Short-form string
            volumes.append(str(entry))
    result: dict[str, Any] = {}
    if volumes:
        result["Volume"] = volumes
    if binds:
        result["Bind"] = binds
    if tmpfs_list:
        result["Tmpfs"] = tmpfs_list
    return result


def convert_tmpfs(value: Any) -> dict[str, Any]:
    """Convert compose ``tmpfs`` to ``Tmpfs`` lines."""
    if value is None:
        return {}
    return {"Tmpfs": [str(v) for v in _as_list(value)]}


def convert_devices(value: Any) -> dict[str, Any]:
    """Convert compose ``devices`` to ``Device`` lines."""
    if value is None:
        return {}
    return {"Device": [str(v) for v in _as_list(value)]}


def convert_dns(value: Any) -> dict[str, Any]:
    """Convert compose ``dns`` to ``DNS`` lines."""
    if value is None:
        return {}
    return {"DNS": [str(v) for v in _as_list(value)]}


def convert_dns_search(value: Any) -> dict[str, Any]:
    """Convert compose ``dns_search`` to ``DNSSearch`` lines."""
    if value is None:
        return {}
    return {"DNSSearch": [str(v) for v in _as_list(value)]}


def convert_extra_hosts(value: Any) -> dict[str, Any]:
    """Convert compose ``extra_hosts`` to ``AddHost`` lines."""
    if value is None:
        return {}
    return {"AddHost": [str(v) for v in _as_list(value)]}


def convert_cap_add(value: Any) -> dict[str, Any]:
    """Convert compose ``cap_add`` to ``AddCapability`` lines."""
    if value is None:
        return {}
    return {"AddCapability": [str(v) for v in _as_list(value)]}


def convert_cap_drop(value: Any) -> dict[str, Any]:
    """Convert compose ``cap_drop`` to ``DropCapability`` lines."""
    if value is None:
        return {}
    return {"DropCapability": [str(v) for v in _as_list(value)]}


def convert_group_add(value: Any) -> dict[str, Any]:
    """Convert compose ``group_add`` to ``GroupAdd`` lines."""
    if value is None:
        return {}
    return {"GroupAdd": [str(v) for v in _as_list(value)]}


def convert_secrets(value: Any) -> dict[str, Any]:
    """Convert compose ``secrets`` to ``Secret`` lines."""
    if value is None:
        return {}
    return {"Secret": [str(v) for v in _as_list(value)]}


def convert_ulimits(value: Any) -> dict[str, Any]:
    """Convert compose ``ulimits`` to ``Ulimit`` lines."""
    if value is None:
        return {}
    ulimits: list[str] = []
    if isinstance(value, dict):
        for name, limit in value.items():
            if isinstance(limit, dict):
                soft = limit.get("soft", limit.get("hard", 0))
                hard = limit.get("hard", soft)
                ulimits.append(f"{name}={soft}:{hard}")
            else:
                ulimits.append(f"{name}={limit}")
    return {"Ulimit": ulimits} if ulimits else {}


def convert_logging(value: Any) -> dict[str, Any]:
    """Convert compose ``logging`` to ``LogDriver`` / ``LogOpt``."""
    if value is None:
        return {}
    result: dict[str, Any] = {}
    if isinstance(value, dict):
        driver = value.get("driver")
        if driver:
            result["LogDriver"] = str(driver)
        options = value.get("options")
        if options and isinstance(options, dict):
            result["LogOpt"] = [f"{k}={v}" for k, v in options.items()]
    return result


def convert_healthcheck(value: Any) -> dict[str, Any]:
    """Convert compose ``healthcheck`` to quadlet health check fields.

    Handles the compose healthcheck dict with ``test``, ``interval``,
    ``timeout``, ``retries``, ``start_period``, and ``disable`` keys.
    """
    if value is None:
        return {}
    result: dict[str, Any] = {}
    if isinstance(value, dict):
        test = value.get("test")
        if test:
            if isinstance(test, list):
                # Remove the CMD/CMD-SHELL prefix if present
                if test and test[0] in ("CMD", "CMD-SHELL"):
                    cmd = " ".join(test[1:]) if len(test) > 1 else ""
                else:
                    cmd = " ".join(test)
                result["HealthCmd"] = cmd
            else:
                result["HealthCmd"] = str(test)

        interval = value.get("interval")
        if interval:
            result["HealthInterval"] = f"{_parse_duration_seconds(interval)}s"

        timeout = value.get("timeout")
        if timeout:
            result["HealthTimeout"] = f"{_parse_duration_seconds(timeout)}s"

        retries = value.get("retries")
        if retries is not None:
            result["HealthRetries"] = str(retries)

        start_period = value.get("start_period")
        if start_period:
            result["HealthStartPeriod"] = f"{_parse_duration_seconds(start_period)}s"

        if value.get("disable"):
            result["HealthCmd"] = "none"
    return result


def convert_networks(value: Any) -> dict[str, Any]:
    """Convert compose ``networks`` to ``Network`` lines."""
    if value is None:
        return {}
    networks: list[str] = []
    if isinstance(value, list):
        networks = [str(v) for v in value]
    elif isinstance(value, dict):
        networks = list(value.keys())
    return {"Network": networks} if networks else {}
