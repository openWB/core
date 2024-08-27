#!/usr/bin/env python3
import logging
import re

from modules.backup_clouds.nextcloud.config import NextcloudBackupCloud, NextcloudBackupCloudConfiguration
from modules.common import req
from modules.common.abstract_device import DeviceDescriptor

log = logging.getLogger(__name__)


def upload_backup(config: NextcloudBackupCloudConfiguration, backup_filename: str, backup_file: bytes) -> None:
    if config.user is None:
        url_match = re.fullmatch(r'(http[s]?):\/\/([\S^/]+)\/(?:index.php\/)?s\/(.+)', config.ip_address)
        if not url_match:
            raise ValueError(f"URL '{config.ip_address}' hat nicht die erwartete Form "
                             "'https://server/index.php/s/user_token' oder 'https://server/s/user_token'")
        upload_url = f"{url_match[1]}://{url_match[2]}"
        user = url_match[url_match.lastindex]
    else:
        upload_url = config.ip_address
        user = config.user

    req.get_http_session().put(
        f'{upload_url}/public.php/webdav/{backup_filename}',
        headers={'X-Requested-With': 'XMLHttpRequest', },
        data=backup_file,
        auth=(user, '' if config.password is None else config.password),
        timeout=30
    )


def create_backup_cloud(config: NextcloudBackupCloud):
    def updater(backup_filename: str, backup_file: bytes):
        upload_backup(config.configuration, backup_filename, backup_file)
    return updater


device_descriptor = DeviceDescriptor(configuration_factory=NextcloudBackupCloud)
