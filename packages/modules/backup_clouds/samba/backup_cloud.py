#!/usr/bin/env python3
import logging
import os
import io
import re
import socket
from smb.SMBConnection import SMBConnection

from modules.backup_clouds.samba.config import SambaBackupCloud, SambaBackupCloudConfiguration
from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_backup_cloud import ConfigurableBackupCloud

log = logging.getLogger(__name__)

def isPortOpen(host, port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        try:
                s.connect((host, int(port)))
                s.shutdown(socket.SHUT_RDWR)
                return True
        except:
                return False
        finally:
                s.close()

def upload_backup(config: SambaBackupCloudConfiguration, backup_filename: str, backup_file: bytes) -> None:
    conn = SMBConnection(config.smb_user, config.smb_password, os.uname()[1], config.smb_server, use_ntlm_v2=True)
    foundedChars = re.search(r'[\\\:\*\?\"\<\>\|]+', config.smb_path)
    isHostReachable = isPortOpen(config.smb_server, 139)

    if foundedChars:
        log.warn("Folgenden ungültige Zeichen im Pfad gefunden: {}".format(foundedChars.group()))
        log.warn("Sicherung nicht erfolgreich.")
        sendFile = False
    else:
        sendFile = True

    if isHostReachable and conn.connect(config.smb_server, 139) and sendFile:
        log.info("SMB Verbindungsaufbau erfolgreich.")
        full_file_path = config.smb_path + backup_filename if config.smb_path is not None else backup_filename
        log.info("Backup nach //" + config.smb_server + '/' + config.smb_share + '/' + full_file_path)
        try:
            conn.storeFile(config.smb_share, full_file_path, io.BytesIO(backup_file))
        except Exception as error:
            log.error(error.__str__().split('\n')[0])
            log.error("Möglicherweise ist die Freigabe oder ein Unterordner nicht vorhanden.")
        conn.close()
    elif sendFile:
        log.warn("SMB Verbindungsaufbau fehlgeschlagen.")
    elif isHostReachable == False:
        log.warn("Host {} und/oder Port 139 nicht zu erreichen.".format(config.smb_server))

def create_backup_cloud(config: SambaBackupCloud):
    def updater(backup_filename: str, backup_file: bytes):
        upload_backup(config.configuration, backup_filename, backup_file)
    return ConfigurableBackupCloud(config=config, component_updater=updater)


device_descriptor = DeviceDescriptor(configuration_factory=SambaBackupCloud)
