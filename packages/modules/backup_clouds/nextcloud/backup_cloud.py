#!/usr/bin/env python3
import logging
import re
from typing import Callable, List, Tuple

from dataclass_utils._dataclass_asdict import asdict
from helpermodules.pub import Pub
from modules.backup_clouds.nextcloud.config import NextcloudBackupCloud, NextcloudBackupCloudConfiguration
from modules.common import req
from modules.common.abstract_device import DeviceDescriptor

log = logging.getLogger(__name__)


def _parse_nextcloud_upload_url_and_user(config: NextcloudBackupCloudConfiguration) -> Tuple[str, str]:
    """
    Liefert Basis-URL (ohne /public.php/webdav/...) und Benutzer (Token oder User).
    Zusätzlich wird der WebDAV-Pfad zum Backup-Verzeichnis zurückgegeben.
    """
    if config.user is None:
        url_match = re.fullmatch(r'(http[s]?):\/\/([\S^/]+)\/(?:index.php\/)?s\/(.+)', config.ip_address)
        if not url_match:
            raise ValueError(
                f"URL '{config.ip_address}' hat nicht die erwartete Form "
                "'https://server/index.php/s/user_token' oder 'https://server/s/user_token'"
            )
        upload_url = f"{url_match[1]}://{url_match[2]}"
        user = url_match[url_match.lastindex]
    else:
        upload_url = config.ip_address
        user = config.user
    return upload_url, user


def _list_backups(config: NextcloudBackupCloudConfiguration,
                  backup_filename: str) -> List[str]:
    """
    Listet alle vorhandenen Backupdateien, die zum gleichen OpenWB-Suffix gehören
    (Pattern-Match am Dateinamen) und gibt eine nach Dateinamen sortierte Liste zurück.
    """
    max_backups = config.max_backups
    if not max_backups or max_backups <= 0:
        return []
    if config.base_path is None:
        return []

    upload_url, user = _parse_nextcloud_upload_url_and_user(config)

    # Robust gruppieren: OpenWB-Backups enden entweder auf ".openwb-backup"
    # oder auf ".openwb-backup.gpg". Der Teil vor dem ersten Punkt kann
    # timestamps-/versionspezifisch sein und darf daher nicht zum Gruppieren
    # verwendet werden.
    base_name = backup_filename.split("/")[-1]
    if base_name.endswith(".openwb-backup.gpg"):
        required_suffix = ".openwb-backup.gpg"
    elif base_name.endswith(".openwb-backup"):
        required_suffix = ".openwb-backup"
    else:
        log.warning("Nextcloud Retention: Unerwartetes Backup-Dateimuster: %s", base_name)
        return []

    # WebDAV PROPFIND, um Dateiliste zu bekommen
    list_path = f"{config.base_path}/"
    response = req.get_http_session().request(
        "PROPFIND",
        f"{upload_url}{list_path}",
        headers={
            "Depth": "1",
            "Content-Type": "text/xml",
        },
        data="""<?xml version="1.0" encoding="utf-8" ?>
<d:propfind xmlns:d="DAV:">
  <d:prop>
    <d:displayname />
  </d:prop>
</d:propfind>""",
        auth=(user, "" if config.password is None else config.password),
        timeout=60,
    )

    if not response.ok:
        log.warning("Nextcloud PROPFIND für Backup-Liste fehlgeschlagen: %s %s",
                    response.status_code, response.reason)
        return []

    # Sehr einfache Auswertung: nach <d:displayname>...</d:displayname> parsen
    # und alle Einträge sammeln, die auf unser Suffix enden.
    names: List[str] = []
    for match in re.finditer(r"<d:displayname>([^<]+)</d:displayname>", response.text):
        name = match.group(1)
        if name.endswith(required_suffix):
            names.append(name)

    # Alphabetisch sortieren – entspricht der im Issue gewünschten Sortierung nach Dateinamen
    names.sort()
    return names


def _enforce_retention(config: NextcloudBackupCloudConfiguration, backup_filename: str) -> None:
    """
    Löscht alte Nextcloud-Backups, so dass höchstens max_backups Dateien mit dem
    gleichen OpenWB-Suffix (Pattern-Match) übrig bleiben. Sortierung erfolgt nach
    Dateinamen, es bleiben die letzten N erhalten.
    """
    max_backups = config.max_backups
    if not max_backups or max_backups <= 0:
        return
    if config.base_path is None:
        return

    upload_url, user = _parse_nextcloud_upload_url_and_user(config)
    all_backups = _list_backups(config, backup_filename)
    if len(all_backups) <= max_backups:
        return

    # Alle außer den letzten max_backups löschen
    to_delete = all_backups[:-max_backups]

    for name in to_delete:
        delete_path = f"{config.base_path}/{name}" if config.base_path else name
        try:
            log.info("Lösche altes Nextcloud-Backup: %s", delete_path)
            resp = req.get_http_session().delete(
                f"{upload_url}{delete_path}",
                headers={"X-Requested-With": "XMLHttpRequest"},
                auth=(user, "" if config.password is None else config.password),
                timeout=60,
            )
            if not resp.ok:
                log.warning("Löschen des Nextcloud-Backups '%s' fehlgeschlagen: %s %s",
                            delete_path, resp.status_code, resp.reason)
        except Exception as error:
            log.error("Fehler beim Löschen alter Nextcloud-Backups (%s): %s",
                      delete_path, str(error).split("\n")[0])


def _put_backup_file(upload_url: str,
                     base_path: str,
                     backup_filename: str,
                     backup_file: bytes,
                     user: str,
                     password: str) -> None:
    req.get_http_session().put(
        f"{upload_url}{base_path}/{backup_filename.lstrip('/')}",
        headers={'X-Requested-With': 'XMLHttpRequest', },
        data=backup_file,
        auth=(user, password),
        timeout=60
    )


def _determine_working_base_path(config: NextcloudBackupCloud,
                                 user: str,
                                 upload_call: Callable[[str], None]) -> None:
    base_path_candidates = ["/public.php/webdav",
                            f"/public.php/dav/files/{user}",
                            "/remote.php/webdav",
                            f"/remote.php/dav/files/{user}"]

    for base_path in [config.configuration.base_path] + base_path_candidates:
        try:
            if base_path:
                upload_call(base_path)
                if base_path != config.configuration.base_path:
                    config.configuration.base_path = base_path
                    Pub().pub("openWB/set/system/backup_cloud/config", asdict(config))
                return
        except Exception as error:
            log.warning("Fehler beim Upload des Nextcloud-Backups mit base_path '%s': %s",
                        base_path, str(error).split("\n")[0])

    raise ValueError("Upload des Nextcloud-Backups mit keinem der üblichen Upload-Pfade erfolgreich. "
                     "Bitte überprüfen Sie die Konfiguration und die Erreichbarkeit der Nextcloud.")


def upload_backup(config: NextcloudBackupCloud, backup_filename: str, backup_file: bytes) -> None:
    upload_url, user = _parse_nextcloud_upload_url_and_user(config.configuration)
    password = '' if config.configuration.password is None else config.configuration.password

    # Erst den bekannten base_path versuchen, dann Kandidaten.
    _determine_working_base_path(config, user,
                                 lambda base_path: _put_backup_file(upload_url,
                                                                    base_path,
                                                                    backup_filename,
                                                                    backup_file,
                                                                    user,
                                                                    password)
                                 )

    # Aufbewahrung alter Backups erzwingen (wenn konfiguriert)
    try:
        _enforce_retention(config.configuration, backup_filename)
    except Exception as error:
        log.error("Fehler bei der Bereinigung alter Nextcloud-Backups: %s",
                  str(error).split("\n")[0])


def create_backup_cloud(config: NextcloudBackupCloud):
    def updater(backup_filename: str, backup_file: bytes):
        upload_backup(config, backup_filename, backup_file)
    return updater


device_descriptor = DeviceDescriptor(configuration_factory=NextcloudBackupCloud)
