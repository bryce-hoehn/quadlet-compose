"""Pydantic model for a Podman Quadlet container unit file (podman-container.unit(5))."""

from typing import ClassVar, Literal

from pydantic import Field

from ._base import QuadletUnit


class ContainerUnit(QuadletUnit):
    """Represents the ``[Container]`` section of a ``.container`` Quadlet unit file.

    Each field maps to a Quadlet ``[Container]`` key and its corresponding
    ``podman run`` CLI flag.

    Reference: https://docs.podman.io/en/latest/markdown/podman-container.unit.5.html
    """

    _section: ClassVar[str] = "Container"
    _scalar_fields: ClassVar[tuple[str, ...]] = (
        "AutoUpdate",
        "CgroupsMode",
        "ContainerName",
        "Entrypoint",
        "EnvironmentHost",
        "Group",
        "HealthCmd",
        "HealthInterval",
        "HealthLogDestination",
        "HealthMaxLogCount",
        "HealthMaxLogSize",
        "HealthOnFailure",
        "HealthRetries",
        "HealthStartPeriod",
        "HealthStartupCmd",
        "HealthStartupInterval",
        "HealthStartupRetries",
        "HealthStartupSuccess",
        "HealthStartupTimeout",
        "HealthTimeout",
        "HostName",
        "HttpProxy",
        "Image",
        "IP",
        "IP6",
        "LogDriver",
        "Memory",
        "NoNewPrivileges",
        "Notify",
        "PidsLimit",
        "Pod",
        "Pull",
        "ReadOnly",
        "ReadOnlyTmpfs",
        "ReloadCmd",
        "ReloadSignal",
        "Retry",
        "RetryDelay",
        "Rootfs",
        "RunInit",
        "SeccompProfile",
        "SecurityLabelDisable",
        "SecurityLabelFileType",
        "SecurityLabelLevel",
        "SecurityLabelNested",
        "SecurityLabelType",
        "ShmSize",
        "StartWithPod",
        "StopSignal",
        "StopTimeout",
        "SubGIDMap",
        "SubUIDMap",
        "Timezone",
        "User",
        "UserNS",
        "WorkingDir",
    )
    _list_fields: ClassVar[tuple[str, ...]] = (
        "AddCapability",
        "AddDevice",
        "AddHost",
        "Annotation",
        "ContainersConfModule",
        "DNS",
        "DNSOption",
        "DNSSearch",
        "DropCapability",
        "Environment",
        "EnvironmentFile",
        "ExposeHostPort",
        "GIDMap",
        "UIDMap",
        "GroupAdd",
        "GlobalArgs",
        "PodmanArgs",
        "Label",
        "LogOpt",
        "Mask",
        "Mount",
        "Network",
        "NetworkAlias",
        "PublishPort",
        "Secret",
        "Sysctl",
        "Tmpfs",
        "Ulimit",
        "Unmask",
        "Volume",
        "Exec",
    )

    # -- Capabilities ----------------------------------------------------------

    AddCapability: list[str] | None = Field(
        default=None,
        description=(
            "Add Linux capabilities (e.g. ``CAP_NET_ADMIN``). "
            "Corresponds to ``--cap-add``. May be specified multiple times."
        ),
    )
    DropCapability: list[str] | None = Field(
        default=None,
        description=(
            "Drop Linux capabilities, or ``all`` to drop all. "
            "Corresponds to ``--cap-drop``. May be specified multiple times."
        ),
    )

    # -- Devices ---------------------------------------------------------------

    AddDevice: list[str] | None = Field(
        default=None,
        description=(
            "Add a host device to the container "
            "(``host-device[:container-device][:permissions]``). "
            "Corresponds to ``--device``. May be specified multiple times."
        ),
    )

    # -- Host resolution -------------------------------------------------------

    AddHost: list[str] | None = Field(
        default=None,
        description=(
            "Custom host-to-IP mapping (``hostname[;hostname...]:ip``). "
            "Corresponds to ``--add-host``. May be specified multiple times."
        ),
    )

    # -- Annotations & labels --------------------------------------------------

    Annotation: list[str] | None = Field(
        default=None,
        description=(
            "Add an annotation (``key=value``). Corresponds to ``--annotation``. "
            "May be specified multiple times."
        ),
    )
    Label: list[str] | None = Field(
        default=None,
        description=(
            "Add metadata labels (``key=value``). Corresponds to ``--label``. "
            "May be specified multiple times."
        ),
    )

    # -- Auto-update -----------------------------------------------------------

    AutoUpdate: Literal["registry", "local"] | None = Field(
        default=None,
        description=(
            "Auto-update policy for ``podman-auto-update(1)``. "
            "``registry`` requires a fully-qualified image reference."
        ),
    )

    # -- Cgroups ---------------------------------------------------------------

    CgroupsMode: Literal["enabled", "disabled", "no-conmon", "split"] | None = Field(
        default=None,
        description=(
            "Determines whether the container creates cgroups. "
            "Default for Quadlets is ``split``."
        ),
    )

    # -- Identity --------------------------------------------------------------

    ContainerName: str | None = Field(
        default=None,
        description=(
            "Assign a name to the container. Defaults to ``systemd-$name``. "
            "Corresponds to ``--name``."
        ),
    )

    # -- containers.conf -------------------------------------------------------

    ContainersConfModule: list[str] | None = Field(
        default=None,
        description=(
            "containers.conf(5) module to load. "
            "Corresponds to ``--module``. May be specified multiple times."
        ),
    )

    # -- DNS -------------------------------------------------------------------

    DNS: list[str] | None = Field(
        default=None,
        description=(
            "Custom DNS server IP addresses. Corresponds to ``--dns``. "
            "May be specified multiple times."
        ),
    )
    DNSOption: list[str] | None = Field(
        default=None,
        description="Custom DNS options. Corresponds to ``--dns-option``.",
    )
    DNSSearch: list[str] | None = Field(
        default=None,
        description="Custom DNS search domains. Corresponds to ``--dns-search``.",
    )

    # -- Entrypoint / exec -----------------------------------------------------

    Entrypoint: str | None = Field(
        default=None,
        description="Override the default ENTRYPOINT from the image. Corresponds to ``--entrypoint``.",
    )
    Exec: list[str] | None = Field(
        default=None,
        description=(
            "Additional arguments after the image specification. "
            "Equivalent to extra args after ``podman run <image>``."
        ),
    )

    # -- Environment -----------------------------------------------------------

    Environment: list[str] | None = Field(
        default=None,
        description=(
            "Set environment variables (``env=value``). Corresponds to ``--env``. "
            "May be specified multiple times."
        ),
    )
    EnvironmentFile: list[str] | None = Field(
        default=None,
        description=(
            "Read environment variables from a file. Corresponds to ``--env-file``. "
            "May be specified multiple times."
        ),
    )
    EnvironmentHost: bool | None = Field(
        default=None,
        description="Use host environment inside the container. Corresponds to ``--env-host``.",
    )

    # -- Ports -----------------------------------------------------------------

    ExposeHostPort: list[str] | None = Field(
        default=None,
        description=(
            "Expose a port or range (``port[-port][/protocol]``). "
            "Corresponds to ``--expose``. May be specified multiple times."
        ),
    )
    PublishPort: list[str] | None = Field(
        default=None,
        description=(
            "Publish a port (``[[ip:]hostPort:]containerPort[/protocol]``). "
            "Corresponds to ``--publish``. May be specified multiple times."
        ),
    )

    # -- User / group namespaces -----------------------------------------------

    GIDMap: list[str] | None = Field(
        default=None,
        description=(
            "GID mapping (``[flags]container_gid:from_gid[:amount]``). "
            "Corresponds to ``--gidmap``. May be specified multiple times. "
            "Conflicts with ``UserNS`` and ``SubGIDMap``."
        ),
    )
    UIDMap: list[str] | None = Field(
        default=None,
        description=(
            "UID mapping (``[flags]container_uid:from_uid[:amount]``). "
            "Corresponds to ``--uidmap``. May be specified multiple times. "
            "Conflicts with ``UserNS`` and ``SubUIDMap``."
        ),
    )
    UserNS: str | None = Field(
        default=None,
        description=(
            "User namespace mode. Corresponds to ``--userns``. "
            "Conflicts with ``GIDMap``, ``UIDMap``, ``SubGIDMap``, ``SubUIDMap``."
        ),
    )
    SubGIDMap: str | None = Field(
        default=None,
        description=(
            "Name of the subgid map. Corresponds to ``--subgidname``. "
            "Conflicts with ``UserNS`` and ``GIDMap``."
        ),
    )
    SubUIDMap: str | None = Field(
        default=None,
        description=(
            "Name of the subuid map. Corresponds to ``--subuidname``. "
            "Conflicts with ``UserNS`` and ``UIDMap``."
        ),
    )
    User: str | None = Field(
        default=None,
        description=(
            "Username or UID (and optionally ``:groupname`` or ``:GID``) "
            "used inside the container. Corresponds to ``--user``."
        ),
    )
    Group: str | None = Field(
        default=None,
        description="Numeric GID to run as inside the container. Corresponds to ``--user UID:GID``.",
    )
    GroupAdd: list[str] | None = Field(
        default=None,
        description=(
            "Assign additional groups to the primary user, or ``keep-groups``. "
            "Corresponds to ``--group-add``. May be specified multiple times."
        ),
    )

    # -- Escape hatches --------------------------------------------------------

    GlobalArgs: list[str] | None = Field(
        default=None,
        description=(
            "Extra arguments passed directly after the ``podman`` command. "
            "Space-separated per entry; may be listed multiple times."
        ),
    )
    PodmanArgs: list[str] | None = Field(
        default=None,
        description=(
            "Extra arguments appended to the end of the ``podman run`` command. "
            "Space-separated per entry; may be listed multiple times."
        ),
    )

    # -- Healthcheck -----------------------------------------------------------

    HealthCmd: str | None = Field(
        default=None,
        description="Healthcheck command. Corresponds to ``--health-cmd``.",
    )
    HealthInterval: str | None = Field(
        default=None,
        description="Healthcheck interval (e.g. ``2m``, ``30s``). Corresponds to ``--health-interval``.",
    )
    HealthLogDestination: str | None = Field(
        default=None,
        description=(
            "Healthcheck log destination (directory path, ``local``, or ``events_logger``). "
            "Corresponds to ``--health-log-destination``."
        ),
    )
    HealthMaxLogCount: int | None = Field(
        default=None,
        description="Maximum number of healthcheck log entries. Corresponds to ``--health-max-log-count``.",
    )
    HealthMaxLogSize: int | None = Field(
        default=None,
        description="Maximum length of stored healthcheck log in characters. Corresponds to ``--health-max-log-size``.",
    )
    HealthOnFailure: Literal["none", "kill", "restart", "stop"] | None = Field(
        default=None,
        description="Action to take when the container transitions to unhealthy.",
    )
    HealthRetries: int | None = Field(
        default=None,
        description="Retries allowed before healthcheck is considered unhealthy. Corresponds to ``--health-retries``.",
    )
    HealthStartPeriod: str | None = Field(
        default=None,
        description=(
            "Initialization time needed for bootstrap (e.g. ``1m``). "
            "Corresponds to ``--health-start-period``."
        ),
    )
    HealthStartupCmd: str | None = Field(
        default=None,
        description="Startup healthcheck command. Corresponds to ``--health-startup-cmd``.",
    )
    HealthStartupInterval: str | None = Field(
        default=None,
        description="Startup healthcheck interval. Corresponds to ``--health-startup-interval``.",
    )
    HealthStartupRetries: int | None = Field(
        default=None,
        description="Startup healthcheck retries before container restart. Corresponds to ``--health-startup-retries``.",
    )
    HealthStartupSuccess: int | None = Field(
        default=None,
        description="Successful runs required before startup healthcheck passes. Corresponds to ``--health-startup-success``.",
    )
    HealthStartupTimeout: str | None = Field(
        default=None,
        description="Startup healthcheck timeout (e.g. ``1m33s``). Corresponds to ``--health-startup-timeout``.",
    )
    HealthTimeout: str | None = Field(
        default=None,
        description="Maximum time allowed for healthcheck (e.g. ``20s``). Corresponds to ``--health-timeout``.",
    )

    # -- Hostname --------------------------------------------------------------

    HostName: str | None = Field(
        default=None,
        description="Hostname inside the container. Corresponds to ``--hostname``.",
    )

    # -- Proxy -----------------------------------------------------------------

    HttpProxy: bool | None = Field(
        default=None,
        description=(
            "Pass proxy environment variables into the container. "
            "Defaults to ``true``. Set to ``false`` to disable."
        ),
    )

    # -- Image (required) ------------------------------------------------------

    Image: str = Field(
        description=(
            "The image to run. Use a fully-qualified image reference for "
            "best results. Special cases: ending with ``.image`` or ``.build`` "
            "links to the corresponding Quadlet unit."
        ),
    )

    # -- IP addresses ----------------------------------------------------------

    IP: str | None = Field(
        default=None,
        description="Static IPv4 address. Corresponds to ``--ip``.",
    )
    IP6: str | None = Field(
        default=None,
        description="Static IPv6 address. Corresponds to ``--ip6``.",
    )

    # -- Logging ---------------------------------------------------------------

    LogDriver: str | None = Field(
        default=None,
        description=(
            "Logging driver (e.g. ``journald``, ``k8s-file``, ``none``). "
            "Corresponds to ``--log-driver``."
        ),
    )
    LogOpt: list[str] | None = Field(
        default=None,
        description=(
            "Logging driver options (``name=value``). Corresponds to ``--log-opt``. "
            "May be specified multiple times."
        ),
    )

    # -- Security: masking / SELinux -------------------------------------------

    Mask: list[str] | None = Field(
        default=None,
        description=(
            "Paths to mask, colon-separated per entry. "
            "Corresponds to ``--security-opt mask=``. May be specified multiple times."
        ),
    )
    NoNewPrivileges: bool | None = Field(
        default=None,
        description="Disable container processes from gaining additional privileges. Corresponds to ``--security-opt no-new-privileges``.",
    )
    SeccompProfile: str | None = Field(
        default=None,
        description=(
            "Seccomp profile path, or ``unconfined`` to disable. "
            "Corresponds to ``--security-opt seccomp=``."
        ),
    )
    SecurityLabelDisable: bool | None = Field(
        default=None,
        description="Turn off label separation for the container. Corresponds to ``--security-opt label=disable``.",
    )
    SecurityLabelFileType: str | None = Field(
        default=None,
        description="Set the label file type for container files. Corresponds to ``--security-opt label=filetype:``.",
    )
    SecurityLabelLevel: str | None = Field(
        default=None,
        description="Set the label process level for container processes. Corresponds to ``--security-opt label=level:``.",
    )
    SecurityLabelNested: bool | None = Field(
        default=None,
        description="Allow security labels to function within the container. Corresponds to ``--security-opt label=nested``.",
    )
    SecurityLabelType: str | None = Field(
        default=None,
        description="Set the label process type for container processes. Corresponds to ``--security-opt label=type:``.",
    )
    Unmask: list[str] | None = Field(
        default=None,
        description=(
            "Paths to unmask (colon-separated), or ``ALL``. "
            "Corresponds to ``--security-opt unmask=``. May be specified multiple times."
        ),
    )

    # -- Memory ----------------------------------------------------------------

    Memory: str | None = Field(
        default=None,
        description=(
            "Memory limit (e.g. ``20g``, ``512m``). Corresponds to ``--memory``."
        ),
    )

    # -- Mounts ----------------------------------------------------------------

    Mount: list[str] | None = Field(
        default=None,
        description=(
            "Attach a filesystem mount (``type=TYPE,TYPE-SPECIFIC-OPTION[,...]``). "
            "Corresponds to ``--mount``. May be specified multiple times."
        ),
    )

    # -- Networking ------------------------------------------------------------

    Network: list[str] | None = Field(
        default=None,
        description=(
            "Network mode (e.g. ``host``, ``bridge``, ``none``, a network name, "
            "or ``ns:<path>``). Corresponds to ``--network``. "
            "May be specified multiple times."
        ),
    )
    NetworkAlias: list[str] | None = Field(
        default=None,
        description=(
            "Network-scoped alias for the container. "
            "Corresponds to ``--network-alias``. May be specified multiple times."
        ),
    )

    # -- Notify ----------------------------------------------------------------

    Notify: Literal["true", "healthy"] | None = Field(
        default=None,
        description=(
            "Enable sd_notify. ``true`` passes notification to the container; "
            "``healthy`` postpones notification until healthcheck passes."
        ),
    )

    # -- PID limits ------------------------------------------------------------

    PidsLimit: int | None = Field(
        default=None,
        description="Container PID limit. Set to ``-1`` for unlimited. Corresponds to ``--pids-limit``.",
    )

    # -- Pod -------------------------------------------------------------------

    Pod: str | None = Field(
        default=None,
        description=(
            "Link to a Quadlet ``.pod`` unit. Value must be ``<name>.pod``. "
            "Corresponds to ``--pod``."
        ),
    )

    # -- Pull policy -----------------------------------------------------------

    Pull: Literal["always", "missing", "never", "newer"] | None = Field(
        default=None,
        description="Pull image policy. Default is ``missing``. Corresponds to ``--pull``.",
    )

    # -- Read-only filesystem --------------------------------------------------

    ReadOnly: bool | None = Field(
        default=None,
        description="Mount the container's root filesystem as read-only. Corresponds to ``--read-only``.",
    )
    ReadOnlyTmpfs: bool | None = Field(
        default=None,
        description=(
            "When read-only, mount tmpfs on /dev, /dev/shm, /run, /tmp, /var/tmp. "
            "Default is ``true``. Corresponds to ``--read-only-tmpfs``."
        ),
    )

    # -- Reload ----------------------------------------------------------------

    ReloadCmd: str | None = Field(
        default=None,
        description=(
            "Add ExecReload running ``podman exec`` with this command. "
            "Mutually exclusive with ``ReloadSignal``."
        ),
    )
    ReloadSignal: str | None = Field(
        default=None,
        description=(
            "Add ExecReload running ``podman kill`` with this signal. "
            "Mutually exclusive with ``ReloadCmd``."
        ),
    )

    # -- Retry -----------------------------------------------------------------

    Retry: int | None = Field(
        default=None,
        description="Number of pull retries. Default is 3. Corresponds to ``--retry``.",
    )
    RetryDelay: str | None = Field(
        default=None,
        description="Delay between retries (e.g. ``5s``). Corresponds to ``--retry-delay``.",
    )

    # -- Rootfs ----------------------------------------------------------------

    Rootfs: str | None = Field(
        default=None,
        description=(
            "Use an exploded container rootfs on the filesystem. "
            "Conflicts with ``Image``. Corresponds to ``--rootfs``."
        ),
    )

    # -- Init ------------------------------------------------------------------

    RunInit: bool | None = Field(
        default=None,
        description="Run an init inside the container that forwards signals and reaps processes. Corresponds to ``--init``.",
    )

    # -- Secrets ---------------------------------------------------------------

    Secret: list[str] | None = Field(
        default=None,
        description=(
            "Give the container access to a secret (``secret[,opt=opt ...]``). "
            "Corresponds to ``--secret``. May be specified multiple times."
        ),
    )

    # -- IPC -------------------------------------------------------------------

    ShmSize: str | None = Field(
        default=None,
        description=(
            "Size of ``/dev/shm`` (e.g. ``64m``, ``1g``). "
            "Corresponds to ``--shm-size``."
        ),
    )

    # -- Pod lifecycle ---------------------------------------------------------

    StartWithPod: bool | None = Field(
        default=None,
        description=(
            "Start the container after the associated pod is created. "
            "Default is ``true``. Only relevant when ``Pod`` is set."
        ),
    )

    # -- Stop ------------------------------------------------------------------

    StopSignal: str | None = Field(
        default=None,
        description="Signal to stop the container. Default is ``SIGTERM``. Corresponds to ``--stop-signal``.",
    )
    StopTimeout: int | None = Field(
        default=None,
        description="Timeout to stop the container in seconds. Default is 10. Corresponds to ``--stop-timeout``.",
    )

    # -- Sysctl ----------------------------------------------------------------

    Sysctl: list[str] | None = Field(
        default=None,
        description=(
            "Configure namespaced kernel parameters (``name=value``). "
            "Corresponds to ``--sysctl``. May be specified multiple times."
        ),
    )

    # -- Timezone --------------------------------------------------------------

    Timezone: str | None = Field(
        default=None,
        description=(
            "Set timezone in container (e.g. ``local``, ``America/New_York``). "
            "Corresponds to ``--tz``."
        ),
    )

    # -- Tmpfs -----------------------------------------------------------------

    Tmpfs: list[str] | None = Field(
        default=None,
        description=(
            "Create a tmpfs mount. Corresponds to ``--tmpfs``. "
            "May be specified multiple times."
        ),
    )

    # -- Ulimit ----------------------------------------------------------------

    Ulimit: list[str] | None = Field(
        default=None,
        description=(
            "Ulimit options (``name=soft[:hard]``). Corresponds to ``--ulimit``. "
            "May be specified multiple times."
        ),
    )

    # -- Volumes ---------------------------------------------------------------

    Volume: list[str] | None = Field(
        default=None,
        description=(
            "Mount a volume in the container "
            "(``[[SOURCE-VOLUME|HOST-DIR:]CONTAINER-DIR[:OPTIONS]]``). "
            "Corresponds to ``--volume``. May be specified multiple times."
        ),
    )

    # -- Working directory -----------------------------------------------------

    WorkingDir: str | None = Field(
        default=None,
        description="Working directory inside the container. Corresponds to ``--workdir``.",
    )
