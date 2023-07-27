#!/usr/bin/env python3
import logging
import time
from subprocess import check_call, Popen, PIPE
from pathlib import Path

from modules.backup_clouds.nfs.config import NfsBackupCloud, NfsBackupCloudConfiguration
from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_backup_cloud import ConfigurableBackupCloud

log = logging.getLogger(__name__)
nfs_mount = '/mnt/nfs_mount'


def call_timeout(cmd: str, timeout: float) -> bool:
    start = time.time()
    p = Popen(cmd)
    while time.time() - start < timeout:
        if p.poll is not None:
            return True
        time.sleep(0.1)
    p.kill()
    log.error('backup-nfs: command ' + cmd + ' timed out')
    return False


def upload_backup(config: NfsBackupCloudConfiguration, backup_filename: str, backup_file: bytes) -> None:
    nfs_share = config.nfs_share

    # create nfs mount folder if not existent
    p = Path(nfs_mount)
    if p.is_dir():
        log.warn('nfs mount folder ' + nfs_mount + ' exists - reuse it')
    else:
        check_call('sudo mkdir ' + nfs_mount, shell=True)
    # check if nfs is mounted already
    cmd = 'mount | grep "' + nfs_share + '" | wc -l'
    p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()
    if int(stdout) != 0:
        log.warn('nfs share seems tio be mounted - reuse it')
    else:
        check_call('sudo mount -t nfs ' + nfs_share + ' ' + nfs_mount, shell=True)

    # copy backup file to nfs share
    check_call('sudo cp /var/www/html/openWB/data/backup/' + backup_filename +
               ' ' + nfs_mount + '/' + backup_filename, shell=True)

    # umount nfs share
    check_call('sudo umount ' + nfs_mount, shell=True)

    # remove mount point
    check_call('sudo rmdir ' + nfs_mount, shell=True)


def create_backup_cloud(config: NfsBackupCloud):
    def updater(backup_filename: str, backup_file: bytes):
        upload_backup(config.configuration, backup_filename, backup_file)
    return ConfigurableBackupCloud(config=config, component_updater=updater)


device_descriptor = DeviceDescriptor(configuration_factory=NfsBackupCloud)
