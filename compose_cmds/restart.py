"""compose_restart - Stop and restart services (down + up)."""

from compose_cmds.down import compose_down
from compose_cmds.up import compose_up


def compose_restart(
    compose_file: str | None = None,
    kube: bool = False,
    remove_orphans: bool = False,
    **_kwargs,
) -> None:
    """Restart services by running down then up.

    Regenerates quadlet files and restarts all containers.
    """
    compose_down(compose_file=compose_file, remove_orphans=remove_orphans)
    compose_up(
        compose_file=compose_file,
        kube=kube,
        detach=True,
        remove_orphans=remove_orphans,
    )
