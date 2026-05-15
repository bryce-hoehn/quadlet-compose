"""ServiceBuild → BuildUnit field mapping table."""

from ..converters import (
    convert_build_context,
    convert_build_dockerfile,
    convert_build_labels,
    convert_build_network,
    convert_build_pull,
    convert_build_secrets,
    convert_build_target,
    convert_list_or_dict_to_build_env,
)

BUILD_FIELD_MAP = [
    ("context", "SetWorkingDirectory", convert_build_context),
    ("dockerfile", "File", convert_build_dockerfile),
    ("target", "Target", convert_build_target),
    ("pull", "Pull", convert_build_pull),
    ("network", "Network", convert_build_network),
    ("args", "Environment", convert_list_or_dict_to_build_env),
    ("secrets", "Secret", convert_build_secrets),
    ("labels", "Label", convert_build_labels),
]
