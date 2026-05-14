"""Service → ContainerUnit field mapping table.

Each entry is ``(compose_attr, quadlet_attr, converter | None)``.
``None`` converter means 1:1 identity (same type, just rename).
Empty ``quadlet_attr`` signals a 1:N expansion (converter returns multiple fields).
"""

from __future__ import annotations

from typing import Any, Callable

from converters import (
    convert_cap_add,
    convert_cap_drop,
    convert_cgroup,
    convert_command,
    convert_container_name,
    convert_devices,
    convert_dns,
    convert_dns_search,
    convert_entrypoint,
    convert_expose,
    convert_extra_hosts,
    convert_group_add,
    convert_healthcheck,
    convert_hostname,
    convert_image,
    convert_init,
    convert_list_or_dict_to_env,
    convert_list_or_dict_to_labels,
    convert_list_or_dict_to_sysctls,
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
    _as_optional_list,
)

#: Type alias for a field-map entry.
Converter = Callable[[Any], dict[str, Any]]
FieldMapEntry = tuple[str, str, Converter | None]

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
