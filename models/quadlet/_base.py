"""Shared base class for Quadlet unit models.

All six Quadlet unit types (``.container``, ``.network``, ``.volume``,
``.pod``, ``.build``, ``.image``) share two behaviours:

* A ``_coerce_list`` validator that wraps a bare ``str`` in ``[str]``
  for fields annotated as ``list[str] | None``.
* A ``to_quadlet()`` serializer that renders the model as an INI-style
  unit file.

Both are provided once here so they are not copy-pasted across every model.
"""

from typing import Any, ClassVar, get_args, get_origin

from pydantic import BaseModel, field_validator
from pydantic_core.core_schema import ValidationInfo


def _is_list_annotation(annotation: Any) -> bool:
    """Return ``True`` if *annotation* includes ``list`` (e.g. ``list[str] | None``)."""
    if get_origin(annotation) is list:
        return True
    return any(get_origin(a) is list for a in get_args(annotation))


class QuadletUnit(BaseModel):
    """Base class for all Quadlet unit models.

    Provides:

    * ``_coerce_list`` validator — wraps a bare string in a list for
      fields annotated as ``list[str] | None``.
    * ``to_quadlet()`` — renders the model as an INI-style unit file.

    Subclasses **must** set the ``ClassVar`` tuples
    ``_section``, ``_scalar_fields``, and ``_list_fields``.
    """

    _section: ClassVar[str] = ""
    _scalar_fields: ClassVar[tuple[str, ...]] = ()
    _list_fields: ClassVar[tuple[str, ...]] = ()

    # -- Validators ------------------------------------------------------------

    @field_validator("*", mode="before")
    @classmethod
    def _coerce_list(cls, v: Any, info: ValidationInfo) -> Any:
        """Allow a single string to be used where a list is expected."""
        if isinstance(v, str) and info.field_name is not None:
            field_info = cls.model_fields.get(info.field_name)
            if field_info is not None and _is_list_annotation(field_info.annotation):
                return [v]
        return v

    # -- Serialisation helpers -------------------------------------------------

    def to_quadlet(self) -> str:
        """Render the model as a Quadlet unit file string.

        Only non-``None`` fields are emitted.  List fields produce one
        line per element.

        Returns:
            The complete ``[{section}]`` unit file content **without** a
            trailing newline.
        """
        lines: list[str] = [f"[{self._section}]"]

        for field_name in self._scalar_fields:
            value = getattr(self, field_name, None)
            if value is not None:
                lines.append(f"{field_name}={value}")

        for field_name in self._list_fields:
            values = getattr(self, field_name, None)
            if values:
                for value in values:
                    lines.append(f"{field_name}={value}")

        return "\n".join(lines)
