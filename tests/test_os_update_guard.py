"""Sandbox the branch fallback; never change a real checkout, service or OS."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class OsUpdateGuardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / 'repo'
        (self.repo / 'runs').mkdir(parents=True)
        (self.repo / 'data/log').mkdir(parents=True)
        self.os_release = self.root / 'os-release'
        self.os_release.write_text('VERSION_CODENAME=bullseye\n')
        self.events = self.root / 'events'
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        self.env = dict(os.environ, PATH=str(self.bin) + ':' + os.environ['PATH'],
                        EVENTS=str(self.events), TAGS='2.5.0\n2.4.1-Patch.2\n2.4.1\n2.3.0',
                        APPLY_STATUS='0', FETCH_STATUS='0')
        for name in ('git', 'sudo', 'sleep', 'mosquitto_pub'):
            script = self.bin / name
            script.write_text('#!/bin/bash\nprintf "%s\\n" "' + name + ' $*" >> "$EVENTS"\n'
                              + ('cat >> "$EVENTS"; printf "\\n" >> "$EVENTS"\n' if name == 'mosquitto_pub' else '')
                              + 'exit 0\n')
            script.chmod(0o755)
        for name in ('atreboot.sh', 'update_self.sh', 'update_version_helpers.sh', 'os_update_guard.sh'):
            source = (ROOT / 'runs' / name).read_text()
            if name == 'os_update_guard.sh':
                source = source.replace('/etc/os-release', str(self.os_release))
            if name == 'update_self.sh':
                # The fake reboot returns immediately. Keep it foregrounded
                # so assertions cannot race the shell's background launch.
                source = source.replace('sudo reboot now &', 'sudo reboot now')
            (self.repo / 'runs' / name).write_text(source)
        with (self.repo / 'runs/update_version_helpers.sh').open('a') as stream:
            stream.write('''
fetchVersionRefs() { echo fetch >> "$EVENTS"; return "$FETCH_STATUS"; }
latestTagByPattern() { printf '%s\\n' "$TAGS" | grep -E -m1 "$1"; }
applyVersion() { echo "apply $*" >> "$EVENTS"; return "$APPLY_STATUS"; }
''')

    def run_bash(self, source):
        return subprocess.run(['bash', '-c', source], env=self.env,
                              capture_output=True, text=True, timeout=10)

    def calls(self):
        return self.events.read_text() if self.events.exists() else ''

    def run_update(self, branch='trixie-next', tag='*HEAD*'):
        result = subprocess.run(['bash', str(self.repo / 'runs/update_self.sh'), branch, tag],
                                env=self.env, capture_output=True, text=True, timeout=10)
        return result

    def test_only_bullseye_and_bookworm_trigger_fallback(self):
        for codename,status in [('bullseye',0),('bookworm',0),('trixie',1),
                                ('forky',1),('buster',1),('',1)]:
            with self.subTest(codename=codename):
                self.os_release.write_text('VERSION_CODENAME="' + codename + '"\n')
                result = self.run_bash('source "' + str(self.repo / 'runs/os_update_guard.sh')
                                       + '"; requiresSystemUpdate')
                self.assertEqual(result.returncode, status, result.stderr)

    def test_unreadable_os_identity_does_not_become_a_release_downgrade(self):
        self.os_release.unlink()
        result = self.run_update()
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('apply ', self.calls())
        self.assertNotIn('sudo reboot', self.calls())

    def test_legacy_os_uses_compatible_release_and_native_notification(self):
        for codename in ('bullseye', 'bookworm'):
            with self.subTest(codename=codename):
                self.events.write_text('')
                self.os_release.write_text('VERSION_CODENAME=' + codename + '\n')
                self.assertEqual(self.run_update(tag='2.5.0').returncode, 0)
                calls = self.calls()
                self.assertIn('refs/tags/2.4.1-Patch.2 Release 0', calls)
                self.assertNotIn('refs/remotes/origin/trixie-next', calls)
                payload = json.loads(next(line for line in calls.splitlines() if line.startswith('{')))
                self.assertEqual(payload['source'], 'command')
                self.assertEqual(payload['type'], 'warning')
                self.assertEqual(payload['message'], 'openWB 2.5.x benötigt ein Systemupdate. '
                                 'Bitte zuerst das OS-Update durchführen. '
                                 'Neustart auf das aktuelle Release wird durchgeführt.')
                self.assertIn('sudo reboot now', calls)
                self.assertLess(calls.index('apply '), calls.index('openWB/system/messages/'))

    def test_missing_compatible_release_or_fetch_failure_never_checkouts_or_reboots(self):
        for updates in ({'TAGS':'3.0.0\n2.5.0\n2.4.1-Beta.1\n2.3.0-RC.1'},
                        {'FETCH_STATUS':'1'}):
            with self.subTest(updates=updates):
                self.events.write_text('')
                env = self.env.copy()
                self.env.update(updates)
                self.assertNotEqual(self.run_update().returncode, 0)
                self.assertNotIn('apply ', self.calls())
                self.assertNotIn('sudo reboot', self.calls())
                self.env = env

    def test_checkout_failure_does_not_announce_or_reboot(self):
        self.env['APPLY_STATUS']='1'
        self.assertNotEqual(self.run_update().returncode, 0)
        self.assertNotIn('openWB/system/messages/', self.calls())
        self.assertNotIn('sudo reboot', self.calls())

    def test_future_os_does_not_trigger_release_fallback(self):
        for codename in ('trixie','forky'):
            with self.subTest(codename=codename):
                self.events.write_text('')
                self.os_release.write_text('VERSION_CODENAME=' + codename + '\n')
                self.assertEqual(self.run_update().returncode, 0)
                self.assertIn('refs/remotes/origin/trixie-next', self.calls())
                self.assertNotIn('openWB/system/messages/', self.calls())

    def test_other_branch_is_not_redirected_on_legacy_os(self):
        self.assertEqual(self.run_update('master').returncode, 0)
        self.assertIn('refs/remotes/origin/master', self.calls())
        self.assertNotIn('openWB/system/messages/', self.calls())

    def test_old_updater_is_caught_before_any_bootstrap_changes(self):
        result = subprocess.run(['bash', str(self.repo / 'runs/atreboot.sh')],
                                env=self.env, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('refs/tags/2.4.1-Patch.2 Release 0',self.calls())
        self.assertFalse((self.repo/'.venvs').exists())
        self.assertFalse((self.repo/'ramdisk').exists())
        self.assertNotIn('apt',self.calls())

    def test_old_updater_recovery_failure_never_enters_bootstrap(self):
        self.env['FETCH_STATUS']='1'
        result = subprocess.run(['bash', str(self.repo / 'runs/atreboot.sh')],
                                env=self.env, capture_output=True, text=True, timeout=10)
        self.assertNotEqual(result.returncode,0)
        self.assertFalse((self.repo/'.venvs').exists())
        self.assertNotIn('sudo reboot',self.calls())

    def test_broker_failure_does_not_prevent_recovery(self):
        (self.bin/'mosquitto_pub').write_text('#!/bin/bash\nexit 1\n')
        self.assertEqual(self.run_update().returncode,0)
        self.assertIn('sudo reboot now',self.calls())


if __name__ == '__main__':
    unittest.main()
