#!/usr/bin/env python3
import logging
from subprocess import Popen, PIPE, CalledProcessError, run
from pathlib import Path

from modules.backup_clouds.nfs.config import NfsBackupCloud, NfsBackupCloudConfiguration
from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_backup_cloud import ConfigurableBackupCloud

log = logging.getLogger(__name__)
nfs_mount = '/mnt/nfs_mount'


# run command as subprocess with timeout, some exception handling and logging
def _run(_cmd: str, _timeout: float, _shell: bool) -> bool:
    log.info('backup-nfs: cmd ' + _cmd + ': starting')
    try:
        p = run([_cmd], timeout=_timeout, stdout=PIPE, stderr=PIPE, shell=_shell)
        p.check_returncode()
    except CalledProcessError as e:
        log.exception('backup-nfs: cmd ' + _cmd + ', Faii: errorcode: '
                      + str(e.returncode) + ', stderr: ' + p.stderr.decode('utf-8'))
        raise e
        return False
    if p.stdout.decode('utf-8') is not None and p.stdout.decode('utf-8') != '':
        log.info('backup-nfs: cmd ' + _cmd + ': Success, stdout: [' + p.stdout.decode('utf-8') + ']')
    else:
        log.info('backup-nfs: cmd ' + _cmd + ': Success')
    return True


def upload_backup(config: NfsBackupCloudConfiguration, backup_filename: str, backup_file: bytes) -> None:
    nfs_share = config.nfs_share

    # create nfs mount folder if not existent
    p = Path(nfs_mount)
    if p.is_dir():
        log.warn('nfs mount folder ' + nfs_mount + ' exists - reuse it')
        rc = True
    else:
        rc = _run('sudo mkdir ' + nfs_mount, 5, True)

    # check if nfs is mounted already
    if rc:
        cmd = 'mount | grep "' + nfs_share + '" | wc -l'
        p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        if int(stdout) != 0:
            log.warn('nfs share seems tio be mounted - reuse it')
        else:
            rc = _run('sudo mount -t nfs ' + nfs_share + ' ' + nfs_mount, 10, True)

    # copy backup file to nfs share
    if rc:
        rc = _run('sudo cp /var/www/html/openWB/data/backup/' + backup_filename +
                  ' ' + nfs_mount + '/' + backup_filename, 5, True)

    # umount nfs share
    if rc:
        rc = _run('sudo umount ' + nfs_mount, 5, True)

    # remove mount point
    if rc:
        rc = _run('sudo rmdir ' + nfs_mount, 5, True)


def create_backup_cloud(config: NfsBackupCloud):
    def updater(backup_filename: str, backup_file: bytes):
        upload_backup(config.configuration, backup_filename, backup_file)
    return ConfigurableBackupCloud(config=config, component_updater=updater)


device_descriptor = DeviceDescriptor(configuration_factory=NfsBackupCloud)
