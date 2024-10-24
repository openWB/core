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
    conn = SMBConnection(config.smb_user, config.smb_password, os.uname()[1], config.smb_server, use_ntlm_v2=True)
    found_invalid_chars = re.search(r'[\\\:\*\?\"\<\>\|]+', config.smb_path)
    host_is_reachable = is_port_open(config.smb_server, 139)

    if found_invalid_chars:
        log.warn("Folgenden ungültige Zeichen im Pfad gefunden: {}".format(found_invalid_chars.group()))
        log.warn("Sicherung nicht erfolgreich.")
        send_file = False
    else:
        send_file = True

    if host_is_reachable and conn.connect(config.smb_server, 139) and send_file:
        log.info("SMB Verbindungsaufbau erfolgreich.")
        full_file_path = config.smb_path + backup_filename if config.smb_path is not None else backup_filename
        log.info("Backup nach //" + config.smb_server + '/' + config.smb_share + '/' + full_file_path)
        try:
            conn.storeFile(config.smb_share, full_file_path, io.BytesIO(backup_file))
        except Exception as error:
            log.error(error.__str__().split('\n')[0])
            log.error("Möglicherweise ist die Freigabe oder ein Unterordner nicht vorhanden.")
        conn.close()
    elif send_file:
        log.warn("SMB Verbindungsaufbau fehlgeschlagen.")
    elif not host_is_reachable:
        log.warn("Host {} und/oder Port 139 nicht zu erreichen.".format(config.smb_server))


def create_backup_cloud(config: SambaBackupCloud):
    def updater(backup_filename: str, backup_file: bytes):
        upload_backup(config.configuration, backup_filename, backup_file)
    return updater


device_descriptor = DeviceDescriptor(configuration_factory=SambaBackupCloud)
