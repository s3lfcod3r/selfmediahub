"""Start im Container: Rechte abgeben, dann die Anwendung starten.

Der Container startet als root - anders liesse sich ein ``/data``-Verzeichnis
aus einer aelteren Installation (das root gehoert) nicht mehr uebernehmen. Bevor
irgendetwas von aussen bedient wird, wechselt der Prozess aber auf einen
unprivilegierten Nutzer: laeuft die Anwendung als root und findet jemand eine
Luecke, gehoert ihm der ganze Container - und alles, was ins Volume geschrieben
wird, gehoert wieder root (genau das Muster, das auf Unraid-Shares regelmaessig
Rechteprobleme macht).

``PUID``/``PGID`` folgen der Unraid-Konvention (Standard 99:100 = nobody:users).
Schlaegt der Wechsel fehl, laeuft die Anwendung weiter - ein Container, der gar
nicht mehr startet, waere das schlechtere Ergebnis. Der Fehlschlag wird
protokolliert.
"""
import logging
import os

logger = logging.getLogger("selfmediahub")


def _own_data_dir(path: str, uid: int, gid: int) -> None:
    """Datenverzeichnis dem Zielnutzer uebereignen (sonst kommt die Anwendung
    nach dem Wechsel nicht mehr an ihre Datenbank)."""
    if not os.path.isdir(path):
        return
    os.chown(path, uid, gid)
    for root, dirs, files in os.walk(path):
        for name in dirs + files:
            try:
                os.chown(os.path.join(root, name), uid, gid)
            except OSError:
                pass


def drop_privileges() -> None:
    if not hasattr(os, "setuid") or os.getuid() != 0:
        return  # kein POSIX oder schon unprivilegiert
    uid = int(os.environ.get("PUID", "99"))
    gid = int(os.environ.get("PGID", "100"))
    if uid == 0:
        logger.warning("PUID=0 gesetzt - die Anwendung laeuft als root.")
        return
    try:
        _own_data_dir(os.environ.get("DATA_DIR", "/data"), uid, gid)
        os.setgroups([])
        os.setgid(gid)
        os.setuid(uid)
        logger.info("Rechte abgegeben: laufe als %s:%s.", uid, gid)
    except OSError:
        logger.exception("Rechtewechsel auf %s:%s fehlgeschlagen - laufe als root weiter.",
                         uid, gid)


if __name__ == "__main__":
    from .main import main

    drop_privileges()
    main()
