"""Pydantic model for a Podman Quadlet network unit file (podman-network.unit(5))."""

from typing import ClassVar

from pydantic import Field

from ._base import QuadletUnit


class NetworkUnit(QuadletUnit):
    """Represents the ``[Network]`` section of a ``.network`` Quadlet unit file.

    Each field maps to a Quadlet ``[Network]`` key and its corresponding
    ``podman network create`` CLI flag.

    Reference: https://docs.podman.io/en/latest/markdown/podman-network.unit.5.html
    """

    _section: ClassVar[str] = "Network"
    _scalar_fields: ClassVar[tuple[str, ...]] = (
        "DisableDNS",
        "Driver",
        "IPAMDriver",
        "IPv6",
        "InterfaceName",
        "Internal",
        "NetworkDeleteOnStop",
        "NetworkName",
        "Options",
    )
    _list_fields: ClassVar[tuple[str, ...]] = (
        "ContainersConfModule",
        "DNS",
        "Gateway",
        "GlobalArgs",
        "IPRange",
        "Label",
        "PodmanArgs",
        "Subnet",
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

    DisableDNS: bool | None = Field(
        default=None,
        description=(
            "Disable the DNS plugin for this network. "
            "Only supported with the bridge driver. Corresponds to ``--disable-dns``."
        ),
    )
    DNS: list[str] | None = Field(
        default=None,
        description=(
            "Custom DNS servers. The special value ``none`` disables creation of "
            "``/etc/resolv.conf`` in the container. Corresponds to ``--dns``. "
            "May be specified multiple times."
        ),
    )

    # -- Driver ----------------------------------------------------------------

    Driver: str | None = Field(
        default=None,
        description=(
            "Network driver (e.g. ``bridge``, ``macvlan``, ``ipvlan``). "
            "Defaults to ``bridge``. Corresponds to ``--driver``."
        ),
    )

    # -- IP configuration ------------------------------------------------------

    Gateway: list[str] | None = Field(
        default=None,
        description=(
            "Gateway for the subnet. Requires a ``Subnet`` option. "
            "Corresponds to ``--gateway``. May be specified multiple times."
        ),
    )
    IPAMDriver: str | None = Field(
        default=None,
        description=(
            "IPAM driver (``dhcp``, ``host-local``, ``none``). "
            "Corresponds to ``--ipam-driver``."
        ),
    )
    IPRange: list[str] | None = Field(
        default=None,
        description=(
            "Allocate container IPs from a range (CIDR or ``startIP-endIP``). "
            "Requires a ``Subnet`` option. Corresponds to ``--ip-range``. "
            "May be specified multiple times."
        ),
    )
    IPv6: bool | None = Field(
        default=None,
        description=("Enable IPv6 (Dual Stack) networking. Corresponds to ``--ipv6``."),
    )
    Subnet: list[str] | None = Field(
        default=None,
        description=(
            "Subnet in CIDR notation. Corresponds to ``--subnet``. "
            "May be specified multiple times."
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
            "Extra arguments appended to the end of the ``podman network create`` "
            "command. Space-separated per entry; may be listed multiple times."
        ),
    )

    # -- Interface / options ---------------------------------------------------

    InterfaceName: str | None = Field(
        default=None,
        description=(
            "Network interface name. For ``bridge`` sets the bridge name; "
            "for ``macvlan``/``ipvlan`` sets the parent device. "
            "Corresponds to ``--interface-name``."
        ),
    )
    Internal: bool | None = Field(
        default=None,
        description=(
            "Restrict external access of this network. Corresponds to ``--internal``."
        ),
    )
    Options: str | None = Field(
        default=None,
        description=(
            "Driver-specific options (e.g. ``isolate=true``, ``mtu=9000``). "
            "Corresponds to ``--opt``."
        ),
    )

    # -- Labels ----------------------------------------------------------------

    Label: list[str] | None = Field(
        default=None,
        description=(
            "OCI labels (``key=value``). Corresponds to ``--label``. "
            "May be specified multiple times."
        ),
    )

    # -- Lifecycle -------------------------------------------------------------

    NetworkDeleteOnStop: bool | None = Field(
        default=None,
        description=(
            "Delete the network when the service is stopped. Defaults to ``false``."
        ),
    )

    # -- Identity --------------------------------------------------------------

    NetworkName: str | None = Field(
        default=None,
        description=(
            "Name of the Podman network. Defaults to ``systemd-$name`` when unset."
        ),
    )
