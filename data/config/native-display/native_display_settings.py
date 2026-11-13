#!/usr/bin/env python3
"""Serialized native display settings, shared by installation and MQTT updates."""
import argparse
from contextlib import contextmanager
import fcntl
import os
from pathlib import Path
import stat
import subprocess
import tempfile

SETTINGS = Path('/home/openwb/native-display/display.ini')
LOCK = Path('/run/lock/openwb-native-display.lock')
UNITS = ('lightdm.service', 'openwb-display-power.service', 'openwb-native-display.service')


def query(name):
    try:
        result = subprocess.run(
            ['mosquitto_sub', '-h', 'localhost', '-p', '1886', '-t',
             'openWB/optional/int_display/' + name, '-C', '1', '-W', '2'],
            capture_output=True, text=True, timeout=4)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def rotation_value(value):
    try:
        degrees = int(value)
    except (TypeError, ValueError):
        return None
    return degrees if degrees in (0, 180) else None


def atomic_write(path, text):
    previous = path.stat() if path.exists() else None
    fd, temporary = tempfile.mkstemp(prefix='.' + path.name + '.', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            os.fchmod(stream.fileno(), stat.S_IMODE(previous.st_mode) if previous else 0o600)
            if previous:
                os.fchown(stream.fileno(), previous.st_uid, previous.st_gid)
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        Path(temporary).unlink(missing_ok=True)


def initialize(path=SETTINGS):
    # The installer owns the shared lock while invoking this as user openwb.
    path.parent.mkdir(mode=0o700, exist_ok=True)
    if path.exists():
        return
    rotation = rotation_value(query('rotation'))
    if rotation is None:
        rotation = 0
    atomic_write(path, '[display]\nrotation=' + str(rotation) + '\nstyle=graphic\n\n'
                 '[mqtt]\nlocalPort=1886\nlocalHttpPort=81\n\n'
                 '[presentation]\noverviewPanel=glass-flow\n')


@contextmanager
def display_lock(inherited_fd=None, path=LOCK):
    # Installer's FD is inherited across exec and refers to the same flock.
    if inherited_fd is None:
        fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    else:
        fd = inherited_fd
        if os.fstat(fd).st_ino != path.stat().st_ino or os.fstat(fd).st_dev != path.stat().st_dev:
            raise ValueError('Unexpected display lock descriptor')
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        if inherited_fd is None:
            os.close(fd)


def systemctl(*args):
    return subprocess.check_output(['systemctl', *args], text=True).strip()


def apply(force=False, new_session=False, reload_power=False):
    # Called only while holding the lock, including all MQTT reads.
    active, detected = query('active'), query('detected')
    if active not in ('true', 'false') or detected not in ('true', 'false'):
        print('Native display state unavailable; current services and boot target preserved.')
        return 'unknown'
    # The application consumes rotation directly from its device-local broker.
    # Do not edit its live QSettings file from a privileged Core helper.
    if active == 'false' or detected == 'false':
        systemctl('stop', 'openwb-native-display.service', 'lightdm.service',
                  'openwb-display-power.service')
        systemctl('disable', *UNITS)
        if systemctl('get-default') != 'multi-user.target':
            systemctl('set-default', 'multi-user.target')
        return 'disabled'
    systemctl('enable', *UNITS)
    if systemctl('get-default') != 'graphical.target':
        systemctl('set-default', 'graphical.target')
    systemctl('restart' if reload_power else 'start', 'openwb-display-power.service')
    systemctl('restart' if new_session else 'start', 'lightdm.service')
    systemctl('restart' if force else 'start', 'openwb-native-display.service')
    systemctl('is-active', '--quiet', *UNITS)
    return 'enabled'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['initialize', 'apply', 'preflight'])
    parser.add_argument('--lock-fd', type=int)
    parser.add_argument('--force', action='store_true')
    parser.add_argument('--new-session', action='store_true')
    parser.add_argument('--reload-power', action='store_true')
    args = parser.parse_args()
    if args.action == 'preflight':
        # Called by the installer while it already holds the shared lock.
        return 0 if all(query(name) in ('true', 'false') for name in ('active', 'detected')) else 75
    if args.action == 'initialize':
        initialize()
    else:
        with display_lock(args.lock_fd):
            print('Native display:', apply(args.force, args.new_session, args.reload_power))


if __name__ == '__main__':
    raise SystemExit(main())
