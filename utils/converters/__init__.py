"""Converter functions for compose-spec → Quadlet value transformations.

Each sub-module groups related converters.  Import from the top-level
package for convenience::

    from converters import convert_ports, convert_healthcheck
"""

from ._helpers import _as_list, _as_optional_list
from ._duration import _parse_duration_seconds
from ._list_or_dict import (
    convert_list_or_dict_to_build_env,
    convert_list_or_dict_to_build_labels,
    convert_list_or_dict_to_env,
    convert_list_or_dict_to_labels,
    convert_list_or_dict_to_sysctls,
)
from .service import (
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
from .build import (
    convert_build_context,
    convert_build_dockerfile,
    convert_build_labels,
    convert_build_network,
    convert_build_pull,
    convert_build_secrets,
    convert_build_target,
)
from .network import (
    convert_network_driver_opts,
    convert_network_enable_ipv6,
    convert_network_internal,
    convert_network_ipam,
    convert_network_labels,
    convert_network_name,
)
from .volume import (
    convert_volume_labels,
    convert_volume_name,
)

__all__ = [
    # helpers
    "_as_list",
    "_as_optional_list",
    "_parse_duration_seconds",
    # list-or-dict
    "convert_list_or_dict_to_env",
    "convert_list_or_dict_to_labels",
    "convert_list_or_dict_to_sysctls",
    "convert_list_or_dict_to_build_env",
    "convert_list_or_dict_to_build_labels",
    # service
    "convert_cap_add",
    "convert_cap_drop",
    "convert_cgroup",
    "convert_command",
    "convert_container_name",
    "convert_devices",
    "convert_dns",
    "convert_dns_search",
    "convert_entrypoint",
    "convert_expose",
    "convert_extra_hosts",
    "convert_group_add",
    "convert_healthcheck",
    "convert_hostname",
    "convert_image",
    "convert_init",
    "convert_logging",
    "convert_mem_limit",
    "convert_networks",
    "convert_pids_limit",
    "convert_ports",
    "convert_pull_policy",
    "convert_read_only",
    "convert_secrets",
    "convert_shm_size",
    "convert_stop_grace_period",
    "convert_stop_signal",
    "convert_tmpfs",
    "convert_ulimits",
    "convert_user",
    "convert_volumes",
    "convert_working_dir",
    # build
    "convert_build_context",
    "convert_build_dockerfile",
    "convert_build_labels",
    "convert_build_network",
    "convert_build_pull",
    "convert_build_secrets",
    "convert_build_target",
    # network
    "convert_network_driver_opts",
    "convert_network_enable_ipv6",
    "convert_network_internal",
    "convert_network_ipam",
    "convert_network_labels",
    "convert_network_name",
    # volume
    "convert_volume_labels",
    "convert_volume_name",
]
