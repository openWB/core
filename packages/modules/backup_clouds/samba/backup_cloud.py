#!/usr/bin/env python3
import logging
import os
import io
from smb.SMBConnection import SMBConnection

from modules.backup_clouds.samba.config import SambaBackupCloud, SambaBackupCloudConfiguration
from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_backup_cloud import ConfigurableBackupCloud

log = logging.getLogger(__name__)


def upload_backup(config: SambaBackupCloudConfiguration, backup_filename: str, backup_file: bytes) -> None:
    smb_path = config.smb_path.split('/')
    conn = SMBConnection(config.smb_user, config.smb_password, os.uname()[1], smb_path[0], use_ntlm_v2=True)
    conn.connect(smb_path[0],139)
    if len(smb_path) <= 2:
        conn.storeFile(smb_path[1], backup_filename.replace(':',''), io.BytesIO(backup_file))
    else:
        foldercount = len(smb_path) - 2
        i = 0
        folder= ""
        while i < foldercount:
            folder = folder + smb_path[(i + foldercount)] + '/'
            i = i + 1
        conn.storeFile(smb_path[1], folder + backup_filename.replace(':',''), io.BytesIO(backup_file))

    conn.close()


def create_backup_cloud(config: SambaBackupCloud):
    def updater(backup_filename: str, backup_file: bytes):
        upload_backup(config.configuration, backup_filename, backup_file)
    return ConfigurableBackupCloud(config=config, component_updater=updater)


device_descriptor = DeviceDescriptor(configuration_factory=SambaBackupCloud)
