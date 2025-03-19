#!/usr/bin/env python3
import logging
import os
import pathlib

from modules.backup_clouds.onedrive.msdrive.onedrive import OneDrive
from modules.backup_clouds.onedrive.api import get_tokens
from modules.backup_clouds.onedrive.config import OneDriveBackupCloud, OneDriveBackupCloudConfiguration
from modules.common.abstract_device import DeviceDescriptor


log = logging.getLogger(__name__)


def upload_backup(config: OneDriveBackupCloudConfiguration, backup_filename: str, backup_file: bytes) -> None:
    # upload a single file to onedrive using credentials from OneDriveBackupCloudConfiguration
    # https://docs.microsoft.com/en-us/onedrive/developer/rest-api/api/driveitem_put_content?view=odsp-graph-online
    tokens = get_tokens(config)  # type: ignore
    log.debug("token object retrieved, access_token: %s", tokens.__len__)
    log.debug("instantiate OneDrive connection")
    onedrive = OneDrive(access_token=tokens["access_token"])

    local_backup = os.path.join(pathlib.Path().resolve(), 'data', 'backup', backup_filename)
    remote_filename = backup_filename.replace(':', '-')  # file won't upload when name contains ':'

    if not config.backuppath.endswith("/"):
        log.debug("fixing  missing ending slash in backuppath: " + config.backuppath)
        config.backuppath = config.backuppath + "/"

    log.debug("uploading file %s to OneDrive", backup_filename)
    onedrive.upload_item(item_path=(config.backuppath+remote_filename), file_path=local_backup,
                         conflict_behavior="replace")


def create_backup_cloud(config: OneDriveBackupCloud):
    def updater(backup_filename: str, backup_file: bytes):
        upload_backup(config.configuration, backup_filename, backup_file)
    return updater


device_descriptor = DeviceDescriptor(configuration_factory=OneDriveBackupCloud)
