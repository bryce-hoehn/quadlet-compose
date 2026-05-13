"""Pydantic model for a Podman Quadlet build unit file (podman-build.unit(5))."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class BuildUnit(BaseModel):
    """Represents the ``[Build]`` section of a ``.build`` Quadlet unit file.

    Each field maps to a Quadlet ``[Build]`` key and its corresponding
    ``podman build`` CLI flag.

    A minimal ``.build`` unit needs at least ``ImageTag`` and either ``File``
    or ``SetWorkingDirectory``.

    Reference: https://docs.podman.io/en/latest/markdown/podman-build.unit.5.html
    """

    # -- containers.conf -------------------------------------------------------

    ContainersConfModule: list[str] | None = Field(
        default=None,
        description=(
            "containers.conf(5) module to load. "
            "Corresponds to ``--module``. May be specified multiple times."
        ),
    )

    # -- Image identity --------------------------------------------------------

    ImageTag: str | None = Field(
        default=None,
        description=(
            "Name assigned to the resulting image. If no registry is given, "
            "``localhost`` is prepended. Corresponds to ``--tag``."
        ),
    )

    # -- Build source ----------------------------------------------------------

    File: str | None = Field(
        default=None,
        description=(
            "Containerfile path or URL. Corresponds to ``--file``. "
            "Use ``-`` to read from stdin."
        ),
    )
    SetWorkingDirectory: str | None = Field(
        default=None,
        description=(
            "Build context directory. Supports a path, URL, or the special "
            "keys ``file`` / ``unit`` to derive the context from the "
            "Containerfile or unit file location."
        ),
    )
    Target: str | None = Field(
        default=None,
        description=("Target build stage to build. Corresponds to ``--target``."),
    )

    # -- Platform selection ----------------------------------------------------

    Arch: str | None = Field(
        default=None,
        description=(
            "Override the architecture of the image to build (e.g. ``aarch64``). "
            "Corresponds to ``--arch``."
        ),
    )
    Variant: str | None = Field(
        default=None,
        description=(
            "Architecture variant of the image (e.g. ``arm/v7``). "
            "Corresponds to ``--variant``."
        ),
    )

    # -- Pull behaviour --------------------------------------------------------

    Pull: Literal["always", "missing", "never", "newer"] | None = Field(
        default=None,
        description=(
            "Pull image policy. ``always`` pulls and errors on failure; "
            "``missing`` pulls only if not local; ``never`` uses local only; "
            "``newer`` pulls if the registry image is newer. "
            "Corresponds to ``--pull``."
        ),
    )
    Retry: int | None = Field(
        default=None,
        description=(
            "Number of times to retry pulling images on failure. "
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

    # -- Authentication --------------------------------------------------------

    AuthFile: str | None = Field(
        default=None,
        description=(
            "Path of the authentication file for registry access. "
            "Corresponds to ``--authfile``."
        ),
    )
    TLSVerify: bool | None = Field(
        default=None,
        description=(
            "Require HTTPS and verify certificates when contacting registries. "
            "Corresponds to ``--tls-verify``."
        ),
    )

    # -- Build environment -----------------------------------------------------

    DNS: list[str] | None = Field(
        default=None,
        description=(
            "Custom DNS servers. The special value ``none`` disables "
            "``/etc/resolv.conf`` creation. Corresponds to ``--dns``. "
            "May be specified multiple times."
        ),
    )
    DNSOption: list[str] | None = Field(
        default=None,
        description=(
            "Custom DNS options. Corresponds to ``--dns-option``. "
            "May be specified multiple times."
        ),
    )
    DNSSearch: list[str] | None = Field(
        default=None,
        description=(
            "Custom DNS search domains. Corresponds to ``--dns-search``. "
            "May be specified multiple times."
        ),
    )
    Environment: list[str] | None = Field(
        default=None,
        description=(
            "Environment variables (``key=value``). Corresponds to ``--env``. "
            "May be specified multiple times."
        ),
    )
    GroupAdd: list[str] | None = Field(
        default=None,
        description=(
            "Additional groups for the primary user (e.g. ``keep-groups``). "
            "Corresponds to ``--group-add``. May be specified multiple times."
        ),
    )
    Network: str | None = Field(
        default=None,
        description=(
            "Network mode for ``RUN`` instructions (e.g. ``host``, ``none``, "
            "``private``). If ending with ``.network``, links to a Quadlet unit. "
            "Corresponds to ``--network``."
        ),
    )
    Secret: list[str] | None = Field(
        default=None,
        description=(
            "Secrets to pass to the build (``id=…[,src=…][,env=…][,type=…]``). "
            "Corresponds to ``--secret``. May be specified multiple times."
        ),
    )
    Volume: list[str] | None = Field(
        default=None,
        description=(
            "Bind mounts (``[SOURCE-VOLUME|HOST-DIR:]CONTAINER-DIR[:OPTIONS]``). "
            "Corresponds to ``--volume``. May be specified multiple times."
        ),
    )

    # -- Build options ---------------------------------------------------------

    Annotation: list[str] | None = Field(
        default=None,
        description=(
            "Image annotations (``annotation=value``). Corresponds to "
            "``--annotation``. May be specified multiple times."
        ),
    )
    ForceRM: bool | None = Field(
        default=None,
        description=(
            "Always remove intermediate containers after a build, even if "
            "the build fails. Default is ``true``. Corresponds to ``--force-rm``."
        ),
    )
    Label: list[str] | None = Field(
        default=None,
        description=(
            "Image labels (``key=value``). Corresponds to ``--label``. "
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
            "Extra arguments appended to the end of the ``podman build`` "
            "command. Space-separated per entry; may be listed multiple times."
        ),
    )

    # -- Validators ------------------------------------------------------------

    @field_validator(
        "Annotation",
        "ContainersConfModule",
        "DNS",
        "DNSOption",
        "DNSSearch",
        "Environment",
        "GlobalArgs",
        "GroupAdd",
        "Label",
        "PodmanArgs",
        "Secret",
        "Volume",
        mode="before",
    )
    @classmethod
    def _coerce_list(cls, v: str | list[str] | None) -> list[str] | None:
        """Allow a single string to be used where a list is expected."""
        if v is None:
            return None
        if isinstance(v, str):
            return [v]
        return v

    # -- Serialisation helpers -------------------------------------------------

    def to_quadlet(self) -> str:
        """Render the model as a Quadlet ``.build`` unit file string.

        Only non-``None`` fields are emitted. List fields produce one
        line per element.

        Returns:
            The complete ``[Build]`` unit file content **without** a trailing
            newline.
        """
        lines: list[str] = ["[Build]"]

        _scalar_fields = (
            "Arch",
            "AuthFile",
            "File",
            "ForceRM",
            "ImageTag",
            "Network",
            "Pull",
            "Retry",
            "RetryDelay",
            "SetWorkingDirectory",
            "Target",
            "TLSVerify",
            "Variant",
        )
        _list_fields = (
            "Annotation",
            "ContainersConfModule",
            "DNS",
            "DNSOption",
            "DNSSearch",
            "Environment",
            "GlobalArgs",
            "GroupAdd",
            "Label",
            "PodmanArgs",
            "Secret",
            "Volume",
        )

        for field_name in _scalar_fields:
            value = getattr(self, field_name, None)
            if value is not None:
                lines.append(f"{field_name}={value}")

        for field_name in _list_fields:
            values = getattr(self, field_name, None)
            if values:
                for value in values:
                    lines.append(f"{field_name}={value}")

        return "\n".join(lines)
