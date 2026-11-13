"""Isolated installer policy tests: no real broker, systemd or backlight writes."""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import threading
import unittest
from unittest.mock import patch

PROFILE = Path(__file__).resolve().parents[1] / 'data/config/native-display'


def load(name):
    spec = importlib.util.spec_from_file_location(name, PROFILE / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


settings = load('native_display_settings')
power = load('display_power_service')


class StateTests(unittest.TestCase):
    def apply(self, active, detected, **kwargs):
        calls = []
        def ctl(*args):
            calls.append(args)
            return 'graphical.target' if args == ('get-default',) else ''
        with patch.object(settings, 'query', side_effect=lambda n: {'active': active, 'detected': detected}[n]), \
                patch.object(settings, 'systemctl', side_effect=ctl):
            result = settings.apply(**kwargs)
        return result, calls

    def test_unknown_does_not_change_any_service_or_boot_setting(self):
        for active, detected in [(None, 'true'), ('true', None), ('', 'true'),
                                 ('false', None), ('TRUE', 'true'), ('true', 'null')]:
            with self.subTest(active=active, detected=detected):
                self.assertEqual(self.apply(active, detected), ('unknown', []))

    def test_disabled_stops_and_disables_boot_activation(self):
        for active, detected in [('false', 'true'), ('true', 'false'), ('false', 'false')]:
            result, calls = self.apply(active, detected, force=True)
            self.assertEqual(result, 'disabled')
            self.assertIn(('disable', *settings.UNITS), calls)
            self.assertIn(('set-default', 'multi-user.target'), calls)
            self.assertTrue(any(c[0] == 'stop' and 'lightdm.service' in c for c in calls))
            self.assertFalse(any(c[0] in ('start', 'restart') for c in calls))

    def test_ordinary_updates_never_restart(self):
        result, calls = self.apply('true', 'true')
        self.assertEqual(result, 'enabled')
        self.assertFalse(any(c[0] == 'restart' for c in calls))

    def test_force_restarts_only_application(self):
        _, calls = self.apply('true', 'true', force=True)
        self.assertEqual([c for c in calls if c[0] == 'restart'],
                         [('restart', 'openwb-native-display.service')])

    def test_new_profile_switches_session(self):
        _, calls = self.apply('true', 'true', new_session=True)
        self.assertIn(('restart', 'lightdm.service'), calls)

    def test_changed_power_helper_restarts_only_when_requested(self):
        _, calls = self.apply('true', 'true', reload_power=True)
        self.assertIn(('restart', 'openwb-display-power.service'), calls)

    def test_local_query_handles_timeout_os_error_and_failure(self):
        for error in [subprocess.TimeoutExpired('mosquitto_sub', 4), OSError('unavailable')]:
            with patch.object(settings.subprocess, 'run', side_effect=error):
                self.assertIsNone(settings.query('rotation'))
        with patch.object(settings.subprocess, 'run', return_value=subprocess.CompletedProcess([], 27, '180')):
            self.assertIsNone(settings.query('rotation'))

    def test_local_query_explicit_transport_and_timeout(self):
        with patch.object(settings.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, '180\n')) as run:
            self.assertEqual(settings.query('rotation'), '180')
        args = run.call_args.args[0]
        self.assertEqual(args[args.index('-h') + 1], 'localhost')
        self.assertEqual(args[args.index('-p') + 1], '1886')

    def test_rotation_only_supported_values(self):
        for raw in ['0', '180']:
            self.assertEqual(settings.rotation_value(raw), int(raw))
        for raw in ['90', '270', '-180', '', None, 'true']:
            self.assertIsNone(settings.rotation_value(raw))

    def test_atomic_initialization_and_existing_settings_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'display.ini'
            with patch.object(settings, 'query', return_value='180'):
                settings.initialize(path)
            self.assertIn('rotation=180\n', path.read_text())
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            path.write_text('[mqtt]\nsecret=keep\n')
            with patch.object(settings, 'query') as query:
                settings.initialize(path)
                query.assert_not_called()
            self.assertEqual(path.read_text(), '[mqtt]\nsecret=keep\n')

    def test_failed_rotation_query_defaults_only_missing_settings(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'display.ini'
            with patch.object(settings, 'query', return_value=None):
                settings.initialize(path)
            self.assertIn('rotation=0\n', path.read_text())

    def test_interrupted_settings_write_does_not_leave_partial_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'display.ini'
            with patch.object(settings.os, 'replace', side_effect=OSError('interrupted')):
                with self.assertRaises(OSError):
                    settings.atomic_write(path, 'incomplete')
            self.assertFalse(path.exists())
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_failed_replace_preserves_existing_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'display.ini'
            path.write_text('keep')
            with patch.object(settings.os, 'replace', side_effect=OSError('interrupted')):
                with self.assertRaises(OSError):
                    settings.atomic_write(path, 'new')
            self.assertEqual(path.read_text(), 'keep')

    def test_shared_lock_serializes_before_reading_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            lock = Path(tmp) / 'lock'
            started, acquired = threading.Event(), threading.Event()
            def waiter():
                started.set()
                with settings.display_lock(path=lock):
                    acquired.set()
            with settings.display_lock(path=lock):
                thread = threading.Thread(target=waiter)
                thread.start()
                self.assertTrue(started.wait(2))
                self.assertFalse(acquired.wait(0.1))
            thread.join(2)
            self.assertTrue(acquired.is_set())
            self.assertFalse(thread.is_alive())

    def test_installer_lock_descriptor_is_reused_without_deadlock(self):
        import os
        import fcntl
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'lock'
            fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
            try:
                fcntl.flock(fd, fcntl.LOCK_EX)
                with settings.display_lock(inherited_fd=fd, path=path):
                    self.assertEqual(os.fstat(fd).st_ino, path.stat().st_ino)
                os.fstat(fd)  # helper must not close the installer's descriptor
            finally:
                os.close(fd)

    def test_enabled_disabled_enabled_transition(self):
        enabled, first = self.apply('true', 'true')
        disabled, middle = self.apply('false', 'true')
        again, last = self.apply('true', 'true')
        self.assertEqual((enabled, disabled, again), ('enabled', 'disabled', 'enabled'))
        self.assertIn(('enable', *settings.UNITS), first)
        self.assertIn(('disable', *settings.UNITS), middle)
        self.assertIn(('enable', *settings.UNITS), last)


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.device = self.root / 'backlight/panel'
        self.device.mkdir(parents=True)
        (self.device / 'brightness').write_text('42')
        (self.device / 'max_brightness').write_text('100')
        self.runtime = self.root / 'runtime'
        self.runtime.mkdir()

    def light(self):
        return power.Backlight(self.device.parent, self.runtime, clock=lambda: 50)

    def test_off_then_on_restores_exact_brightness(self):
        light = self.light()
        light.handle({'op': 'off'})
        self.assertEqual((self.device / 'brightness').read_text(), '0')
        light.handle({'op': 'on'})
        self.assertEqual((self.device / 'brightness').read_text(), '42')

    def test_restart_recovers_completed_record(self):
        self.light().handle({'op': 'off'})
        light = self.light()
        self.assertFalse(light.recovery_error)
        self.assertEqual((self.device / 'brightness').read_text(), '42')

    def test_corrupt_record_does_not_crash_or_invent_brightness(self):
        for contents in ['', '{', 'null', '[]', '{"device":"other","brightness":42}']:
            with self.subTest(contents=contents):
                record = self.runtime / 'restore.json'
                record.write_text(contents)
                (self.device / 'brightness').write_text('0')
                light = self.light()
                self.assertTrue(light.handle({'op': 'status'})['recovery_error'])
                self.assertFalse(light.status()['available'])
                for op in ['on', 'off']:
                    with self.assertRaises(ValueError):
                        light.handle({'op': op})
                self.assertEqual((self.device / 'brightness').read_text(), '0')
                self.assertEqual(record.read_text(), contents)

    def test_interrupted_record_does_not_switch_off_panel(self):
        light = self.light()
        with patch.object(power.os, 'replace', side_effect=OSError('interrupted')):
            with self.assertRaises(OSError):
                light.handle({'op': 'off'})
        self.assertEqual((self.device / 'brightness').read_text(), '42')
        self.assertEqual(list(self.runtime.iterdir()), [])

    def test_orphan_temporary_record_does_not_block_restart(self):
        (self.runtime / '.restore-interrupted').write_text('{')
        light = self.light()
        self.assertFalse(light.recovery_error)
        light.handle({'op': 'off'})
        light.handle({'op': 'on'})
        self.assertEqual((self.device / 'brightness').read_text(), '42')


if __name__ == '__main__':
    unittest.main()
