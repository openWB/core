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


def upload_backup(config: SambaBackupCloudConfiguration, backup_filename: str, backup_file: bytes) -> None:
    SMB_PORT_445 = 445
    SMB_PORT_139 = 139

    # Pfad prüfen
    if re.search(r'[\\\:\*\?\"\<\>\|]+', config.smb_path):
        log.warning("Ungültige Zeichen im Pfad.")
        log.warning("Sicherung nicht erfolgreich.")
        return

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

                return
            except Exception as error:
                raise Exception("Freigabe oder Unterordner existiert möglicherweise nicht. "+str(error).split('\n')[0])
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
