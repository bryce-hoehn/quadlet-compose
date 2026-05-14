"""Pydantic model for a Podman Quadlet pod unit file (podman-pod.unit(5))."""

from typing import ClassVar, Literal

from pydantic import Field

from ._base import QuadletUnit


class PodUnit(QuadletUnit):
    """Represents the [Pod] section of a ``.pod`` Quadlet unit file.

    Each field maps to a Quadlet ``[Pod]`` key and its corresponding
    ``podman pod create`` CLI flag.

    Reference: https://docs.podman.io/en/latest/markdown/podman-pod.unit.5.html
    """

    _section: ClassVar[str] = "Pod"
    _scalar_fields: ClassVar[tuple[str, ...]] = (
        "HostName",
        "IP",
        "IP6",
        "PodName",
        "ServiceName",
        "ExitPolicy",
        "UserNS",
        "SubGIDMap",
        "SubUIDMap",
        "ShmSize",
    )
    _list_fields: ClassVar[tuple[str, ...]] = (
        "AddHost",
        "DNS",
        "DNSOption",
        "DNSSearch",
        "Network",
        "NetworkAlias",
        "PublishPort",
        "GIDMap",
        "UIDMap",
        "Label",
        "Volume",
        "ContainersConfModule",
        "GlobalArgs",
        "PodmanArgs",
    )

    # -- Host resolution -------------------------------------------------------

    AddHost: list[str] | None = Field(
        default=None,
        description=(
            "Custom host-to-IP mapping (hostname[;hostname...]:ip). "
            "Corresponds to ``--add-host``. May be specified multiple times."
        ),
    )
    HostName: str | None = Field(
        default=None,
        description="Hostname inside the pod. Corresponds to ``--hostname``.",
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

    # -- Networking ------------------------------------------------------------

    Network: list[str] | None = Field(
        default=None,
        description=(
            'Network mode for the pod (e.g. "host", "bridge", "none", '
            'a network name, or "ns:<path>"). '
            "Corresponds to ``--network``. May be specified multiple times."
        ),
    )
    NetworkAlias: list[str] | None = Field(
        default=None,
        description=(
            "Network-scoped alias for the pod. "
            "Corresponds to ``--network-alias``. May be specified multiple times."
        ),
    )
    IP: str | None = Field(
        default=None,
        description="Static IPv4 address. Corresponds to ``--ip``.",
    )
    IP6: str | None = Field(
        default=None,
        description="Static IPv6 address. Corresponds to ``--ip6``.",
    )
    PublishPort: list[str] | None = Field(
        default=None,
        description=(
            "Publish a port (``[[ip:]hostPort:]containerPort[/protocol]``). "
            "Corresponds to ``--publish``. May be specified multiple times."
        ),
    )

    # -- Pod identity ----------------------------------------------------------

    PodName: str | None = Field(
        default=None,
        description=(
            "Name of the Podman pod. Defaults to ``systemd-$name`` when unset. "
            "Corresponds to ``--name``."
        ),
    )
    ServiceName: str | None = Field(
        default=None,
        description=(
            "Override the systemd service unit name (without ``.service``). "
            "Default is ``$name-pod``."
        ),
    )

    # -- Exit behaviour --------------------------------------------------------

    ExitPolicy: Literal["stop", "continue"] | None = Field(
        default=None,
        description=(
            "Exit policy when the last container exits. "
            "Default for Quadlets is ``stop``."
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
            "UID mapping (``container_uid:from_uid[:amount]``). "
            "Corresponds to ``--uidmap``. May be specified multiple times. "
            "Conflicts with ``UserNS`` and ``SubUIDMap``."
        ),
    )
    UserNS: str | None = Field(
        default=None,
        description=(
            "User namespace mode for all containers in the pod. "
            "Corresponds to ``--userns``."
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

    # -- Labels ----------------------------------------------------------------

    Label: list[str] | None = Field(
        default=None,
        description=(
            "Metadata labels (``key=value``). Corresponds to ``--label``. "
            "May be specified multiple times."
        ),
    )

    # -- Volumes ---------------------------------------------------------------

    Volume: list[str] | None = Field(
        default=None,
        description=(
            "Bind mount (``[[SOURCE-VOLUME|HOST-DIR:]CONTAINER-DIR[:OPTIONS]]``). "
            "Corresponds to ``--volume``. May be specified multiple times."
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

    # -- Containers.conf -------------------------------------------------------

    ContainersConfModule: list[str] | None = Field(
        default=None,
        description=(
            "containers.conf(5) module to load. "
            "Corresponds to ``--module``. May be specified multiple times."
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
            "Extra arguments appended to the end of the ``podman pod create`` "
            "command. Space-separated per entry; may be listed multiple times."
        ),
    )
