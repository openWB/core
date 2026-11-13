"""Run installer orchestration in a filesystem sandbox with fake system tools."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]

DISPATCH = r'''
import json, os, pathlib, subprocess, sys
name = pathlib.Path(sys.argv[0]).name
args = sys.argv[1:]
with open(os.environ['EVENTS'], 'a') as stream:
    stream.write(json.dumps([name, *args]) + '\n')
if name == 'dpkg':
    print(os.environ.get('ARCHITECTURE', 'arm64'))
elif name == 'id':
    print('1000')
elif name == 'dpkg-query':
    if args[-1] == 'lightdm':
        if os.environ.get('LIGHTDM_PRESENT') == '1':
            print('installed')
        else:
            sys.exit(1)
    elif os.environ.get('PACKAGE_PRESENT') != '1':
        sys.exit(1)
    else:
        print('installed 0.1.0~alpha3+watermark20261113.1')
elif name == 'dpkg-deb':
    print({'Package': 'openwb-native-display', 'Architecture': 'arm64',
           'Version': '0.1.0~alpha3+watermark20261113.1'}[args[-1]])
elif name == 'curl':
    pathlib.Path(args[args.index('--output') + 1]).write_bytes(b'fake package')
elif name == 'sha256sum':
    sys.stdin.read()
elif name == 'sudo':
    if args[:2] == ['-u', 'openwb']:
        args = args[2:]
    sys.exit(subprocess.call(args))
elif name == 'python3':
    if 'preflight' in args:
        sys.exit(int(os.environ.get('PREFLIGHT_STATUS', '75')))
elif name == 'systemctl':
    root = pathlib.Path(os.environ['TARGET_ROOT'])
    if args[0] == 'show':
        unit = args[1]
        present = ((root / ('etc/systemd/system/' + unit)).exists() or
                   (unit == 'lightdm.service' and os.environ.get('LIGHTDM_PRESENT') == '1'))
        print('loaded' if present else 'not-found')
    if args[0] == 'start' and args[1] == 'lightdm.service':
        pending = root / 'etc/openwb/native-display-activation-pending'
        dropin = root / 'etc/systemd/system/lightdm.service.d/20-openwb-provisioning.conf'
        blocked = dropin.exists() and pending.exists() and 'ConditionPathExists=!' in dropin.read_text()
        with open(os.environ['EVENTS'], 'a') as stream:
            stream.write(json.dumps(['activation-blocked' if blocked else 'activated', args[1]]) + '\n')
    if args == ['start', 'openwb2'] and os.environ.get('REBOOT_AT_CORE') == '1':
        # End the parent installer just as a host reboot ends its SSH session.
        os.kill(os.getppid(), 15)
elif name == 'apt-get' and 'install' in args:
    if os.environ.get('POSTINST_START') == '1':
        subprocess.check_call(['systemctl', 'enable', 'lightdm.service'])
        subprocess.check_call(['systemctl', 'start', 'lightdm.service'])
    sys.exit(int(os.environ.get('APT_STATUS', '0')))
'''


class InstallOrderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        self.events = self.root / 'events'
        self.env = dict(os.environ, PATH=str(self.bin) + ':' + os.environ['PATH'],
                        EVENTS=str(self.events), TARGET_ROOT=str(self.root), OPENWB_APT_INDEX_READY='1')
        dispatch = self.bin / 'dispatch'
        dispatch.write_text('#!' + sys.executable + '\n' + DISPATCH)
        dispatch.chmod(0o755)
        for name in ['dpkg', 'id', 'dpkg-query', 'dpkg-deb', 'curl', 'sha256sum',
                     'sudo', 'python3', 'systemctl', 'apt-get', 'sync']:
            (self.bin / name).symlink_to(dispatch)
        self.repo = self.root / 'repo'
        (self.repo / 'runs').mkdir(parents=True)
        shutil.copytree(ROOT / 'data/config/native-display', self.repo / 'data/config/native-display')
        for path in ['etc/systemd/system', 'etc', 'run/lock']:
            (self.root / path).mkdir(parents=True, exist_ok=True)
        (self.root / 'etc/os-release').write_text('VERSION_CODENAME=trixie\n')
        connector = self.root / 'sys/class/drm/card0-DSI-1'
        connector.mkdir(parents=True)
        (connector / 'status').write_text('connected\n')
        (connector / 'modes').write_text('800x480\n')

    def sandbox(self, text):
        return re.sub(r'/(?:etc|usr|run|sys|var|home)/',
                      lambda match: str(self.root) + match.group(), text)

    def calls(self):
        return [json.loads(line) for line in self.events.read_text().splitlines()]

    def prepare_install(self):
        source = (ROOT / 'runs/install_native_display.sh').read_text()
        # Only sandbox adaptation: pretend root and redirect all target paths.
        source = self.sandbox(source.replace('EUID != 0', '0 != 0'))
        script = self.repo / 'runs/install_native_display.sh'
        script.write_text(source)
        return script

    def install(self, *args):
        script = self.prepare_install()
        return self.run_install(script, *args)

    def run_install(self, script, *args):
        return subprocess.run(['bash', str(script), *args], env=self.env,
                              capture_output=True, text=True, timeout=15)

    def test_install_only_provisions_without_broker_or_service_start(self):
        result = self.install('--install-only')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        calls = self.calls()
        self.assertFalse(any(c[0] == 'python3' and 'preflight' in c for c in calls))
        self.assertFalse(any(c[0] == 'python3' and 'apply' in c for c in calls))
        self.assertFalse(any(c[0] == 'systemctl' and c[1] in ('start', 'restart', 'enable', 'set-default') for c in calls))
        self.assertTrue((self.root / 'etc/systemd/system/openwb-native-display.service').exists())
        self.assertTrue((self.root / 'usr/local/lib/openwb-native-display/native_display_settings.py').exists())
        self.assertIn(['systemctl', 'disable', 'lightdm.service',
                       'openwb-native-display.service', 'openwb-display-power.service'], calls)
        self.assertTrue((self.root / 'etc/openwb/native-display-activation-pending').exists())

    def test_standalone_unknown_state_keeps_existing_deferral(self):
        result = self.install()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('installation deferred', result.stdout)
        self.assertFalse(any(c[0] in ('apt-get', 'systemctl') for c in self.calls()))

    def test_standalone_known_state_still_applies(self):
        self.env['PREFLIGHT_STATUS'] = '0'
        result = self.install()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(any(c[0] == 'python3' and 'apply' in c for c in self.calls()))

    def test_invalid_option_has_no_installation_side_effects(self):
        script = self.prepare_install()
        before = self.snapshot()
        result = self.run_install(script, '--invalid')
        self.assertEqual(result.returncode, 2)
        self.assertFalse(self.events.exists())
        self.assertEqual(self.snapshot(), before)

    def snapshot(self):
        return {str(p.relative_to(self.root)): (p.lstat().st_mode,
                os.readlink(p) if p.is_symlink() else p.read_bytes() if p.is_file() else None)
                for p in self.root.rglob('*')}

    def test_preexisting_lightdm_is_stopped_and_disabled_before_packages(self):
        self.env['LIGHTDM_PRESENT'] = '1'
        result = self.install('--install-only')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        calls = self.calls()
        apt = next(i for i, c in enumerate(calls) if c[0] == 'apt-get')
        self.assertLess(calls.index(['systemctl', 'stop', 'lightdm.service']), apt)
        self.assertLess(calls.index(['systemctl', 'disable', 'lightdm.service']), apt)
        self.assertTrue((self.root / 'etc/openwb/native-display-activation-pending').exists())

    def test_package_service_start_is_blocked_for_new_and_existing_lightdm(self):
        for present in ('0', '1'):
            with self.subTest(present=present):
                self.env.update(LIGHTDM_PRESENT=present, POSTINST_START='1')
                result = self.install('--install-only')
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertNotIn(['activated', 'lightdm.service'], self.calls())
                self.assertIn(['activation-blocked', 'lightdm.service'], self.calls())
                self.assertIn(['systemctl', 'disable', 'lightdm.service',
                               'openwb-native-display.service', 'openwb-display-power.service'], self.calls())

    def test_package_failure_keeps_persistent_activation_guard(self):
        self.env.update(POSTINST_START='1', APT_STATUS='1', LIGHTDM_PRESENT='1')
        result = self.install('--install-only')
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue((self.root / 'etc/openwb/native-display-activation-pending').exists())
        self.assertNotIn(['activated', 'lightdm.service'], self.calls())

    def test_existing_native_profile_stops_all_units_before_provisioning(self):
        self.env.update(LIGHTDM_PRESENT='1', PACKAGE_PRESENT='1')
        folder = self.root / 'etc/openwb'
        folder.mkdir(parents=True)
        (folder / 'display-managed-externally').touch()
        for unit in ['openwb-native-display.service', 'openwb-display-power.service']:
            (self.root / 'etc/systemd/system' / unit).touch()
        result = self.install('--install-only')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        calls = self.calls()
        for unit in ['lightdm.service', 'openwb-native-display.service', 'openwb-display-power.service']:
            self.assertIn(['systemctl', 'stop', unit], calls)
            self.assertIn(['systemctl', 'disable', unit], calls)
        self.assertFalse(any(c[0] == 'python3' and 'apply' in c for c in calls))

    def test_activation_guard_survives_loss_of_runtime_directory(self):
        result = self.install('--install-only')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        # A reboot drops /run, but must not drop the service start conditions.
        shutil.rmtree(self.root / 'run')
        result = subprocess.run(['systemctl', 'start', 'lightdm.service'], env=self.env,
                                capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(['activation-blocked', 'lightdm.service'], self.calls())
        self.assertNotIn(['activated', 'lightdm.service'], self.calls())

    def test_current_unsupported_profile_has_distinct_status(self):
        self.env['ARCHITECTURE'] = 'armhf'
        result = self.install('--install-only')
        self.assertEqual(result.returncode, 10, result.stderr)
        self.assertFalse(any(c[0] in ('apt-get', 'systemctl') for c in self.calls()))

    def run_install_tail(self, fail_install=False, reboot=False, unsupported=False):
        source = (ROOT / 'openwb-install.sh').read_text()
        before, tail = source.split('# Complete provisioning', 1)
        self.assertNotIn('systemctl start openwb', before)
        self.assertNotIn('systemctl enable openwb', before)
        fake = self.repo / 'runs/install_native_display.sh'
        fake.write_text('echo "[\\"provision\\", \\"$1\\"]" >> "$EVENTS"\n'
                        + ('exit 1\n' if fail_install else 'exit 10\n' if unsupported
                           else 'touch "$OPENWBBASEDIR/provision-complete"\n'))
        self.env['OPENWBBASEDIR'] = str(self.repo)
        self.env['REBOOT_AT_CORE'] = '1' if reboot else '0'
        folder = self.root / 'etc/openwb'
        folder.mkdir(parents=True)
        (folder / 'display-managed-externally').touch()
        helper = self.root / 'usr/local/lib/openwb-native-display/native_display_settings.py'
        helper.parent.mkdir(parents=True)
        helper.touch()
        return subprocess.run(['bash', '-c', self.sandbox('# Complete provisioning' + tail)],
                              env=self.env, capture_output=True, text=True, timeout=15)

    def test_provisioning_precedes_all_core_service_starts(self):
        result = self.run_install_tail()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        calls = self.calls()
        provision = calls.index(['provision', '--install-only'])
        starts = [i for i, c in enumerate(calls) if c[:2] == ['systemctl', 'start']]
        self.assertEqual(len(starts), 3)
        self.assertTrue(all(provision < i for i in starts))
        enable = calls.index(['systemctl', 'enable', 'openwb2', 'openwb-simpleAPI', 'openwbRemoteSupport'])
        self.assertTrue(provision < enable < starts[0])
        self.assertTrue((self.repo / 'provision-complete').exists())
        self.assertTrue(any(c[0] == 'python3' and 'apply' in c for c in calls[starts[-1] + 1:]))

    def test_failed_provisioning_never_starts_core_services(self):
        result = self.run_install_tail(fail_install=True)
        self.assertEqual(result.returncode, 1)
        self.assertFalse(any(c[:2] == ['systemctl', 'start'] for c in self.calls()))
        self.assertFalse(any(c[:2] == ['systemctl', 'enable'] for c in self.calls()))

    def test_unsupported_run_does_not_activate_stale_marker_and_helper(self):
        result = self.run_install_tail(unsupported=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(any(c[0] == 'python3' and 'apply' in c for c in self.calls()))

    def test_reboot_during_core_start_cannot_interrupt_provisioning(self):
        result = self.run_install_tail(reboot=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue((self.repo / 'provision-complete').exists())
        self.assertIn(['systemctl', 'start', 'openwb2'], self.calls())


if __name__ == '__main__':
    unittest.main()
