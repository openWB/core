#!/usr/bin/env python3
"""Restricted backlight control, with renewable off lease and fail-open restore."""
import json
import os
from pathlib import Path
import signal
import socketserver
import threading
import tempfile
import time

RUNTIME = Path('/run/openwb-display-power')
BACKLIGHT = Path('/sys/class/backlight')
LEASE_SECONDS = 20


class Backlight:
    def __init__(self, root=BACKLIGHT, runtime=RUNTIME, clock=time.monotonic):
        self.root, self.runtime, self.clock = root, runtime, clock
        self.lock = threading.RLock()
        self.deadline = 0
        self.device = None
        self.previous = None
        self.restore_file = runtime / 'restore.json'
        self.recovery_error = False
        # Only a single unambiguous kernel backlight. No client-provided paths.
        devices = [p for p in root.iterdir() if (p / 'brightness').is_file()
                   and (p / 'max_brightness').is_file()] if root.exists() else []
        if len(devices) == 1:
            self.device = devices[0]
        if self.restore_file.exists():
            try:
                record = json.loads(self.restore_file.read_text())
                if self.device is None or record.get('device') != self.device.name:
                    raise ValueError('Backlight changed')
                self.previous = self.valid_brightness(record['brightness'])
                self.restore()
            except (ValueError, TypeError, KeyError, AttributeError, OSError):
                # Keep evidence, serve status, and refuse writes. Never guess a
                # brightness or repeatedly crash on the same corrupt record.
                self.recovery_error = True
                self.previous = None
                self.deadline = 0

    def valid_brightness(self, value):
        maximum = int((self.device / 'max_brightness').read_text())
        if type(value) is not int or not 0 <= value <= maximum:
            raise ValueError('Invalid brightness')
        return value

    def status(self):
        return dict(ok=True, available=self.device is not None and not self.recovery_error,
                    recovery_error=self.recovery_error,
                    off=self.previous is not None,
                    device=self.device.name if self.device else '')

    def restore(self):
        with self.lock:
            if self.previous is not None:
                (self.device / 'brightness').write_text(str(self.previous))
                self.previous = None
                self.deadline = 0
                self.restore_file.unlink(missing_ok=True)

    def handle(self, request):
        if not isinstance(request, dict) or set(request) != {'op'} or request['op'] not in ('status', 'on', 'off'):
            raise ValueError('Only status/on/off accepted')
        with self.lock:
            if self.recovery_error and request['op'] != 'status':
                raise ValueError('Backlight recovery requires inspection')
            if request['op'] == 'on':
                self.restore()
            elif request['op'] == 'off':
                if self.device is None:
                    raise ValueError('No unambiguous kernel backlight available')
                if self.previous is None:
                    value = self.valid_brightness(int((self.device / 'brightness').read_text()))
                    # Do not take ownership of a panel already off for another reason.
                    if value == 0:
                        raise ValueError('Backlight already off outside this service')
                    fd, temporary = tempfile.mkstemp(prefix='.restore-', dir=self.runtime)
                    try:
                        with os.fdopen(fd, 'w') as f:
                            json.dump(dict(device=self.device.name, brightness=value), f)
                            f.flush(); os.fsync(f.fileno())
                        os.replace(temporary, self.restore_file)
                        directory = os.open(self.runtime, os.O_RDONLY | os.O_DIRECTORY)
                        try:
                            os.fsync(directory)
                        finally:
                            os.close(directory)
                    finally:
                        Path(temporary).unlink(missing_ok=True)
                    self.previous = value
                    try:
                        (self.device / 'brightness').write_text('0')
                    except OSError:
                        self.restore()
                        raise
                self.deadline = self.clock() + LEASE_SECONDS
            return self.status()

    def expire(self):
        with self.lock:
            if self.previous is not None and self.clock() >= self.deadline:
                self.restore()


class Handler(socketserver.StreamRequestHandler):
    def handle(self):
        self.request.settimeout(2)
        try:
            line = self.rfile.readline(1025)
            if len(line) > 1024 or not line.endswith(b'\n'):
                raise ValueError('Invalid request')
            response = self.server.backlight.handle(json.loads(line))
        except (ValueError, OSError, TypeError, KeyError):
            response = dict(ok=False, error='Backlight action unavailable')
        self.wfile.write(json.dumps(response).encode() + b'\n')


def main():
    os.umask(0o077)
    light = Backlight()
    path = RUNTIME / 'control.sock'
    path.unlink(missing_ok=True)
    stop = threading.Event()
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda *_: stop.set())
    with socketserver.UnixStreamServer(str(path), Handler) as server:
        server.backlight = light
        server.timeout = 0.5
        os.chmod(path, 0o660)
        try:
            while not stop.is_set():
                server.handle_request()
                light.expire()
        finally:
            light.restore()
            path.unlink(missing_ok=True)


if __name__ == '__main__':
    main()
