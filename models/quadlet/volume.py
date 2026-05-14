"""Pydantic model for a Podman Quadlet volume unit file (podman-volume.unit(5))."""

from pydantic import BaseModel, Field, field_validator


class VolumeUnit(BaseModel):
    """Represents the ``[Volume]`` section of a ``.volume`` Quadlet unit file.

    Each field maps to a Quadlet ``[Volume]`` key and its corresponding
    ``podman volume create`` CLI flag.

    Reference: https://docs.podman.io/en/latest/markdown/podman-volume.unit.5.html
    """

    # -- containers.conf -------------------------------------------------------

    ContainersConfModule: list[str] | None = Field(
        default=None,
        description=(
            "containers.conf(5) module to load. "
            "Corresponds to ``--module``. May be specified multiple times."
        ),
    )

    # -- Volume content --------------------------------------------------------

    Copy: bool | None = Field(
        default=None,
        description=(
            "Copy image content at the mount point into the volume on first run. "
            "Default is ``true``. Corresponds to ``--opt copy``."
        ),
    )

    # -- Device / filesystem ---------------------------------------------------

    Device: str | None = Field(
        default=None,
        description="Path of a device to mount for the volume. Corresponds to ``--opt device=``.",
    )
    Type: str | None = Field(
        default=None,
        description="Filesystem type of ``Device`` (mount ``-t`` option). Corresponds to ``--opt type=``.",
    )
    Options: str | None = Field(
        default=None,
        description="Mount options for the filesystem (mount ``-o`` option). Corresponds to ``--opt o=``.",
    )

    # -- Driver ---------------------------------------------------------------

    Driver: str | None = Field(
        default=None,
        description=(
            "Volume driver name (e.g. ``image``, ``local``). "
            "When set to ``image``, ``Image`` must also be set. "
            "Corresponds to ``--driver``."
        ),
    )

    # -- Escape hatches -------------------------------------------------------

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
            "Extra arguments appended to the end of the ``podman volume create`` "
            "command. Space-separated per entry; may be listed multiple times."
        ),
    )

    # -- Ownership ------------------------------------------------------------

    Group: str | None = Field(
        default=None,
        description=(
            "Host GID or group name for the volume. Corresponds to ``--opt group=``."
        ),
    )
    User: str | None = Field(
        default=None,
        description=(
            "Host UID or user name for the volume. Corresponds to ``--opt uid=``."
        ),
    )

    # -- Image (for Driver=image) ---------------------------------------------

    Image: str | None = Field(
        default=None,
        description=(
            "Image the volume is based on when ``Driver`` is ``image``. "
            "Ending with ``.image`` links to the corresponding Quadlet unit."
        ),
    )

    # -- Labels ---------------------------------------------------------------

    Label: list[str] | None = Field(
        default=None,
        description=(
            "OCI labels (``key=value``). Corresponds to ``--label``. "
            "May be specified multiple times."
        ),
    )

    # -- Identity -------------------------------------------------------------

    VolumeName: str | None = Field(
        default=None,
        description=(
            "Name of the Podman volume. Defaults to ``systemd-$name`` when unset."
        ),
    )

    # -- Validators ------------------------------------------------------------

    @field_validator(
        "ContainersConfModule",
        "GlobalArgs",
        "PodmanArgs",
        "Label",
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
        """Render the model as a Quadlet ``.volume`` unit file string.

        Only non-``None`` fields are emitted. List fields produce one
        line per element.

        Returns:
            The complete ``[Volume]`` unit file content **without** a trailing
            newline.
        """
        lines: list[str] = ["[Volume]"]

        _list_fields = (
            "ContainersConfModule",
            "GlobalArgs",
            "PodmanArgs",
            "Label",
        )
        _scalar_fields = (
            "Copy",
            "Device",
            "Driver",
            "Group",
            "Image",
            "Options",
            "Type",
            "User",
            "VolumeName",
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
