#!/usr/bin/env python3
import logging

from docs.samples.sample_backup_cloud.config import SampleBackupCloud, SampleBackupCloudConfiguration
from modules.common import req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_backup_cloud import ConfigurableBackupCloud

log = logging.getLogger(__name__)


def upload_backup(config: SampleBackupCloudConfiguration, backup_filename: str, backup_file: bytes) -> None:
    # upload backup
    req.get_http_session().put()


def create_backup_cloud(config: SampleBackupCloud):
    def updater(backup_filename: str, backup_file: bytes):
        upload_backup(config.configuration, backup_filename, backup_file)
    return ConfigurableBackupCloud(config=config, component_updater=updater)


device_descriptor = DeviceDescriptor(configuration_factory=SampleBackupCloud)
