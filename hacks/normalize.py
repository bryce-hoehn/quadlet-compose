"""Normalize service fields for podlet compatibility.

Strips or transforms compose fields that podlet cannot handle:

- Strip image tags when a digest is also present
  (``image:foo:v1@sha256:abc`` → ``image:foo@sha256:abc``).
- Strip ``hostname`` and ``network_mode``
  (incompatible with shared pod UTS/network namespaces).
- Fix ``depends_on`` entries with unsupported conditions
  (``service_healthy``, ``service_completed_successfully``) and
  ``restart: true`` without ``required: true``.  Preserves
  ``required`` and ``restart`` flags that podlet translates to
  systemd ``Requires=`` / ``BindsTo=``.
- Strip ``configs`` (not supported by podlet).
- Strip non-external ``secrets`` (only external secrets supported).
"""

from . import _iter_services

_UNSUPPORTED_CONDITIONS = {"service_healthy", "service_completed_successfully"}


def normalize_service_fields(data: dict) -> None:
    """Apply per-service field normalizations that podlet cannot handle."""
    for _name, svc in _iter_services(data):
        # Strip image tag when digest is present
        image = svc.get("image")
        if isinstance(image, str) and "@" in image and ":" in image.split("@")[0]:
            at_idx = image.index("@")
            last_colon = image.rfind(":", 0, at_idx)
            if last_colon > 0:
                svc["image"] = image[:last_colon] + image[at_idx:]

        # Strip pod-incompatible fields
        for key in ("hostname", "network_mode"):
            svc.pop(key, None)

        # Fix depends_on — only strip what podlet can't handle
        dep = svc.get("depends_on")
        if isinstance(dep, dict):
            cleaned = {}
            all_reduced = True
            for dep_name, dep_config in dep.items():
                if not isinstance(dep_config, dict):
                    cleaned[dep_name] = dep_config
                    continue
                # Strip unsupported conditions (defaults to service_started)
                if dep_config.get("condition") in _UNSUPPORTED_CONDITIONS:
                    dep_config.pop("condition", None)
                # restart=true without required=true is unsupported by podlet
                if dep_config.get("restart") and not dep_config.get("required"):
                    dep_config.pop("restart", None)
                if dep_config:
                    cleaned[dep_name] = dep_config
                    all_reduced = False
                else:
                    cleaned[dep_name] = None
            # If all entries were reduced to None, use short form
            if all_reduced:
                svc["depends_on"] = list(cleaned.keys())
            else:
                svc["depends_on"] = cleaned

        # Strip configs (not supported by podlet)
        svc.pop("configs", None)

        # Strip non-external secrets
        secrets = svc.get("secrets")
        if isinstance(secrets, list):
            external = [s for s in secrets if isinstance(s, dict) and s.get("external")]
            if external:
                svc["secrets"] = external
            else:
                svc.pop("secrets", None)
