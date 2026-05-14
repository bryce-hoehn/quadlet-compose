"""Pydantic model for a Podman Quadlet image unit file (podman-image.unit(5))."""

from typing import ClassVar, Literal

from pydantic import Field

from ._base import QuadletUnit


class ImageUnit(QuadletUnit):
    """Represents the ``[Image]`` section of a ``.image`` Quadlet unit file.

    Each field maps to a Quadlet ``[Image]`` key and its corresponding
    ``podman image pull`` CLI flag.

    Reference: https://docs.podman.io/en/latest/markdown/podman-image.unit.5.html
    """

    _section: ClassVar[str] = "Image"
    _scalar_fields: ClassVar[tuple[str, ...]] = (
        "AllTags",
        "Arch",
        "AuthFile",
        "CertDir",
        "Creds",
        "DecryptionKey",
        "Image",
        "ImageTag",
        "OS",
        "Policy",
        "Retry",
        "RetryDelay",
        "TLSVerify",
        "Variant",
    )
    _list_fields: ClassVar[tuple[str, ...]] = (
        "ContainersConfModule",
        "GlobalArgs",
        "PodmanArgs",
    )

    # -- containers.conf -------------------------------------------------------

    ContainersConfModule: list[str] | None = Field(
        default=None,
        description=(
            "containers.conf(5) module to load. "
            "Corresponds to ``--module``. May be specified multiple times."
        ),
    )

    # -- Pull behaviour --------------------------------------------------------

    AllTags: bool | None = Field(
        default=None,
        description=(
            "Pull all tagged images in the repository. "
            "Corresponds to ``--all-tags``."
        ),
    )
    Policy: Literal["always", "missing", "never", "newer"] | None = Field(
        default=None,
        description=(
            "Pull policy. ``always`` pulls and errors on failure; ``missing`` "
            "pulls only if not in local storage; ``never`` uses local only; "
            "``newer`` pulls if the registry image is newer. "
            "Corresponds to ``--policy``."
        ),
    )
    Retry: int | None = Field(
        default=None,
        description=(
            "Number of times to retry pulling the image on failure. "
            "Default is 3. Corresponds to ``--retry``."
        ),
    )
    RetryDelay: str | None = Field(
        default=None,
        description=(
            "Duration of delay between retry attempts (e.g. ``10s``). "
            "Corresponds to ``--retry-delay``."
        ),
    )

    # -- Image identity --------------------------------------------------------

    Image: str | None = Field(
        default=None,
        description=(
            "The image to pull. Supports ``:tag`` and digests. "
            "For archive sources use a ``docker-archive:`` / ``oci-archive:`` prefix."
        ),
    )
    ImageTag: str | None = Field(
        default=None,
        description=(
            "Fully Qualified Image Name (FQIN) of the referenced image. "
            "Only meaningful when the source is a file or directory archive."
        ),
    )

    # -- Platform selection ----------------------------------------------------

    Arch: str | None = Field(
        default=None,
        description=(
            "Override the architecture of the image to pull (e.g. ``aarch64``). "
            "Corresponds to ``--arch``."
        ),
    )
    OS: str | None = Field(
        default=None,
        description=(
            "Override the OS of the image to pull (e.g. ``windows``). "
            "Corresponds to ``--os``."
        ),
    )
    Variant: str | None = Field(
        default=None,
        description=(
            "Architecture variant of the container image (e.g. ``arm/v7``). "
            "Corresponds to ``--variant``."
        ),
    )

    # -- Authentication --------------------------------------------------------

    AuthFile: str | None = Field(
        default=None,
        description=(
            "Path of the authentication file for registry access. "
            "Corresponds to ``--authfile``."
        ),
    )
    CertDir: str | None = Field(
        default=None,
        description=(
            "Path to certificates (``*.crt``, ``*.cert``, ``*.key``) for "
            "connecting to the registry. Corresponds to ``--cert-dir``."
        ),
    )
    Creds: str | None = Field(
        default=None,
        description=(
            "``username[:password]`` for registry authentication. "
            "Corresponds to ``--creds``."
        ),
    )
    DecryptionKey: str | None = Field(
        default=None,
        description=(
            "``key[:passphrase]`` for decryption of images. "
            "Corresponds to ``--decryption-key``."
        ),
    )
    TLSVerify: bool | None = Field(
        default=None,
        description=(
            "Require HTTPS and verify certificates when contacting registries. "
            "Corresponds to ``--tls-verify``."
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
            "Extra arguments appended to the end of the ``podman image pull`` "
            "command. Space-separated per entry; may be listed multiple times."
        ),
    )
