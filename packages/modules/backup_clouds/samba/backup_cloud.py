#!/usr/bin/env python3
import logging
import re
from smb.SMBConnection import SMBConnection
from io import BytesIO

from modules.backup_clouds.samba.config import SambaBackupCloud, SambaBackupCloudConfiguration
from modules.common import req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_backup_cloud import ConfigurableBackupCloud

log = logging.getLogger(__name__)


def upload_backup(config: SambaBackupCloudConfiguration, backup_filename: str, backup_file: bytes) -> None:
    conn = SMBConnection(config.smb_user, config.smb_password, 'client', 'server', use_ntlm_v2=True)
    conn.connect(config.smb_path, 445)

    with conn.openFile(backup_filename, 'w') as file:
        file.write(backup_file)

    conn.close()


def create_backup_cloud(config: SambaBackupCloud):
    def updater(backup_filename: str, backup_file: bytes):
        upload_backup(config.configuration, backup_filename, backup_file)
    return ConfigurableBackupCloud(config=config, component_updater=updater)


device_descriptor = DeviceDescriptor(configuration_factory=SambaBackupCloud)
