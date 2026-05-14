"""Volume → VolumeUnit field mapping table."""

from ..converters import (
    convert_volume_labels,
    convert_volume_name,
)

VOLUME_FIELD_MAP = [
    ("name", "VolumeName", convert_volume_name),
    ("driver", "Driver", lambda v: {"Driver": str(v)} if v else {}),
    ("labels", "Label", convert_volume_labels),
]
