#!/usr/bin/env python3
import logging
import os
import io
import re
import socket

from helpermodules.utils.error_handling import ImportErrorContext
with ImportErrorContext():
    from smb.SMBConnection import SMBConnection

from modules.backup_clouds.samba.config import SambaBackupCloud, SambaBackupCloudConfiguration
from modules.common.abstract_device import DeviceDescriptor

log = logging.getLogger(__name__)


def is_port_open(host: str, port: int):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3)
    try:
        s.connect((host, port))
        s.shutdown(socket.SHUT_RDWR)
        return True
    except Exception:
        return False
    finally:
        s.close()


def _enforce_retention(conn, config: SambaBackupCloudConfiguration, backup_filename: str) -> None:
    """
    Löscht alte Backups auf dem SMB-Share, wenn mehr als max_backups vorhanden sind.
    Es werden nur Dateien berücksichtigt, deren Dateiname mit dem Basisnamen der aktuellen
    Backup-Datei beginnt (alles vor dem ersten Punkt).
    """
    max_backups = getattr(config, "max_backups", None)
    if not max_backups or max_backups <= 0:
        return

    # Verzeichnis ermitteln, in dem die Backups liegen
    smb_path = config.smb_path or "/"
    smb_path = smb_path.rstrip("/")
    if smb_path == "":
        dir_path = "/"
    else:
        dir_path = smb_path

    # Basispräfix der aktuellen Backup-Datei (z.B. "openwb-backup-2026-02-10" aus "openwb-backup-2026-02-10.tar.gz")
    base_name = os.path.basename(backup_filename)
    base_prefix = base_name.split(".")[0]

    # Alle Einträge im Backup-Verzeichnis holen
    entries = conn.listPath(config.smb_share, dir_path)

    # Nur relevante Backup-Dateien herausfiltern
    backup_files = [
        e for e in entries
        if not e.isDirectory
        and e.filename not in (".", "..")
        and e.filename.startswith(base_prefix)
    ]

    if len(backup_files) <= max_backups:
        return

    # Nach Änderungszeit sortieren (neueste zuerst)
    backup_files.sort(key=lambda e: e.last_write_time, reverse=True)

    # Ältere Backups über dem Limit löschen
    for old_entry in backup_files[max_backups:]:
        if dir_path in ("", "/"):
            delete_path = f"/{old_entry.filename}"
        else:
            delete_path = f"{dir_path.rstrip('/')}/{old_entry.filename}"
        try:
            log.info("Lösche altes Samba-Backup: //%s/%s%s", config.smb_server, config.smb_share, delete_path)
            conn.deleteFiles(config.smb_share, delete_path)
        except Exception as error:
            # Fehler beim Aufräumen sollen das eigentliche Backup nicht fehlschlagen lassen
            log.error("Fehler beim Löschen alter Samba-Backups (%s): %s", delete_path, str(error).split("\n")[0])


def upload_backup(config: SambaBackupCloudConfiguration, backup_filename: str, backup_file: bytes) -> None:
    SMB_PORT_445 = 445
    SMB_PORT_139 = 139

    # Pfad prüfen
    if re.search(r'[\\\:\*\?\"\<\>\|]+', config.smb_path):
        raise Exception("Ungültige Zeichen im Pfad. Sicherung nicht erfolgreich.")

    # ------------------------------------------------------------
    # 1) SMB2/3 über Port 445 testen
    # ------------------------------------------------------------
    if is_port_open(config.smb_server, SMB_PORT_445):
        conn = SMBConnection(
            config.smb_user,
            config.smb_password,
            os.uname()[1],
            config.smb_server,
            use_ntlm_v2=True,
            is_direct_tcp=True
        )

        if conn.connect(config.smb_server, SMB_PORT_445):
            try:
                log.info("SMB-Verbindung über Port 445 erfolgreich.")
                full_file_path = f"{config.smb_path.rstrip('/')}/{backup_filename}"
                log.info(f"Backup nach //{config.smb_server}/{config.smb_share}/{full_file_path}")

                conn.storeFile(config.smb_share, full_file_path, io.BytesIO(backup_file))

                try:
                    _enforce_retention(conn, config, backup_filename)
                except Exception as error:
                    log.error(
                        "Fehler bei der Bereinigung alter Samba-Backups (Port 445): %s",
                        str(error).split("\n")[0],
                    )

                return
            except Exception as error:
                raise Exception(
                    "Freigabe oder Unterordner existiert möglicherweise nicht. " + str(error).split("\n")[0]
                )
            finally:
                conn.close()
        else:
            raise Exception("SMB-Verbindungsaufbau über Port 445 nicht möglich.")

    # ------------------------------------------------------------
    # 2) Fallback: SMB1 über Port 139
    # ------------------------------------------------------------
    if not is_port_open(config.smb_server, SMB_PORT_139):
        raise Exception(
            f"Host {config.smb_server} und/oder Port {SMB_PORT_139} und {SMB_PORT_445} nicht erreichbar."
        )

    conn = SMBConnection(
        config.smb_user,
        config.smb_password,
        os.uname()[1],
        config.smb_server,
        use_ntlm_v2=True
    )

    if conn.connect(config.smb_server, SMB_PORT_139):
        try:
            log.info("SMB Verbindungsaufbau über Port 139 erfolgreich.")
            full_file_path = f"{config.smb_path.rstrip('/')}/{backup_filename}"
            log.info(f"Backup nach //{config.smb_server}/{config.smb_share}/{full_file_path}")

            conn.storeFile(config.smb_share, full_file_path, io.BytesIO(backup_file))

            try:
                _enforce_retention(conn, config, backup_filename)
            except Exception as error:
                log.error(
                    "Fehler bei der Bereinigung alter Samba-Backups (Port 139): %s",
                    str(error).split("\n")[0],
                )
        except Exception as error:
            raise Exception(
                "Möglicherweise ist die Freigabe oder ein Unterordner nicht vorhanden."
                + str(error).split("\n")[0]
            )

        finally:
            conn.close()
    else:
        raise Exception("SMB Verbindungsaufbau über Port 139 fehlgeschlagen.")


def create_backup_cloud(config: SambaBackupCloud):
    def updater(backup_filename: str, backup_file: bytes):
        upload_backup(config.configuration, backup_filename, backup_file)
    return updater


device_descriptor = DeviceDescriptor(configuration_factory=SambaBackupCloud)
