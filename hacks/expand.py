"""Expand single-value entries for podlet compatibility.

Docker-compose allows short forms like ``devices: ["/dev/dri"]`` or
``ports: ["8080"]``.  Podlet requires the full ``host:container`` form.
"""

from . import _iter_services


def expand_single_values(data: dict) -> None:
    """Auto-expand single-value entries in devices, ports, and volumes."""
    for _name, svc in _iter_services(data):
        # Expand devices and ports (simple colon duplication)
        for key in ("devices", "ports"):
            items = svc.get(key)
            if not isinstance(items, list):
                continue
            svc[key] = [
                f"{item}:{item}" if isinstance(item, str) and ":" not in item else item
                for item in items
            ]

        # Expand volumes (only path-like single values)
        vols = svc.get("volumes")
        if isinstance(vols, list):
            new_vols = []
            for vol in vols:
                if isinstance(vol, str) and ":" not in vol:
                    # Named volumes have no / or . prefix — leave them alone
                    if "/" in vol or vol.startswith("."):
                        new_vols.append(f"{vol}:{vol}")
                    else:
                        new_vols.append(vol)
                else:
                    new_vols.append(vol)
            svc["volumes"] = new_vols
