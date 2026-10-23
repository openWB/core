"""Exercise the Bash CLI with isolated paths and mocked appliance commands."""

import fcntl
import os
from pathlib import Path
import subprocess
import shutil
import socket
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, build_opener

import pytest


SCRIPT = Path(__file__).with_name("manage_web_php.sh")


@pytest.fixture
def appliance(tmp_path):
    root = tmp_path
    apache = root / "apache"
    for directory in ("mods-enabled", "mods-available", "sites-enabled", "conf-available", "conf-enabled"):
        (apache / directory).mkdir(parents=True)
    for module in ("php7.4", "php8.2"):
        (apache / "mods-enabled" / (module + ".load")).touch()
        (apache / "mods-available" / (module + ".load")).touch()
    for site in ("localhost", "000-default", "apache-openwb-ssl", "http-api-ssl"):
        (apache / "sites-enabled" / (site + ".conf")).touch()
    (root / "web").mkdir()
    (root / "active").touch()
    (root / "bin").mkdir()
    mock = root / "bin/mock"
    mock.write_text(r'''#!/bin/bash
set -eu
echo "${0##*/} $*" >>"$ROOT/commands"
case ${0##*/} in
systemctl)
    case $1 in
    is-enabled) echo enabled ;;
    is-active) test -e "$ROOT/active" ;;
    stop)
        if test -e "$ROOT/fail-stop"; then exit 1; fi
        rm -f "$ROOT/active" ;;
    start) touch "$ROOT/active" ;;
    show) if test -e "$ROOT/active"; then echo active; else echo inactive; fi ;;
    esac ;;
apache2ctl)
    if [[ $1 == -M ]]; then
        for file in "$ROOT"/apache/mods-enabled/php*.load; do
            test -e "$file" || continue
            echo " php_module (shared)"
        done
        if test -e "$ROOT/alternate"; then echo " proxy_fcgi_module (shared)"; fi
    elif test -e "$ROOT/fail-config" && ! test -e "$ROOT/active"; then exit 1
    fi ;;
a2enconf)
    test ! -e "$ROOT/fail-guard" || exit 1
    ln -sf "../conf-available/$1.conf" "$ROOT/apache/conf-enabled/$1.conf" ;;
a2disconf) rm -f "$ROOT/apache/conf-enabled/$1.conf" ;;
a2dismod) rm -f "$ROOT/apache/mods-enabled/$1.load" ;;
a2enmod) touch "$ROOT/apache/mods-enabled/$1.load" ;;
a2dissite) rm -f "$ROOT/apache/sites-enabled/$1.conf" ;;
a2ensite) touch "$ROOT/apache/sites-enabled/$1.conf" ;;
curl)
    url=${!#}
    if test -e "$ROOT/fail-http"; then printf '500'
    elif [[ $url == */index.html ]]; then printf '200'
    elif [[ $url == */uploadFile.php ]]; then printf '403'
    else
        sed -n "s/<?php echo '\([^']*\)';/\1/p" "$ROOT/web/${url##*/}"
        printf '200'
    fi ;;
php) echo "PHP 7.4.33 (cli)" ;;
dpkg-query) echo "Apache PHP package: vendor-version" ;;
esac
''')
    mock.chmod(0o755)
    for name in ("systemctl", "apache2ctl", "a2enconf", "a2disconf", "a2enmod", "a2dismod",
                 "a2ensite", "a2dissite", "curl", "php", "dpkg-query"):
        (root / "bin" / name).symlink_to(mock)
    # Substitute only environment boundaries in the test copy; production paths remain fixed.
    text = SCRIPT.read_text()
    text = text.replace("export PATH=/usr/sbin:/usr/bin:/sbin:/bin",
                        'export PATH="$ROOT/bin:/usr/sbin:/usr/bin:/sbin:/bin"')
    text = text.replace('BASE=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)', 'BASE="$ROOT"')
    for original, replacement in (
        ("/etc/apache2", str(apache)), ("/var/lib/openwb-web-php-bash", str(root / "state")),
        ("/run/openwb-apache", str(root / "lock")),
    ):
        text = text.replace(original, replacement)
    text = text.replace('[[ $EUID == 0 ]]', '[[ 0 == 0 ]]')
    text = text.replace('[[ $(stat -c %u "$STATE") == 0 ]]', '[[ 0 == 0 ]]')
    (root / "script.sh").write_text(text)
    return root


def invoke(root, mode, *options):
    return subprocess.run(["bash", str(root / "script.sh"), mode, *options], capture_output=True, text=True,
                          env={**os.environ, "ROOT": str(root)}, timeout=15)


@pytest.mark.parametrize("api", [True, False])
def test_round_trip_repeated_runs_and_order(appliance, api):
    root = appliance
    site = root / "apache/sites-enabled/http-api-ssl.conf"
    if not api:
        site.unlink()
    for mode in ("disable", "disable", "enable", "enable"):
        result = invoke(root, mode)
        assert result.returncode == 0, result.stdout + result.stderr
        assert "CONFIRMED" in result.stdout
        assert "UNKNOWN" in result.stdout
        assert "INFO:" not in result.stdout
        assert "DIAGNOSTIC:" not in result.stderr
        assert "Usage:" not in result.stdout
    assert site.exists() == api
    assert sorted(p.stem for p in (root / "apache/mods-enabled").glob("*.load")) == ["php7.4", "php8.2"]
    assert not (root / "state/state").exists()
    assert not list((root / "web").iterdir())
    calls = (root / "commands").read_text().splitlines()
    assert calls.index("systemctl stop apache2.service") < calls.index("a2enconf disable-web-php")
    assert calls.index("a2enconf disable-web-php") < calls.index("a2dismod php7.4")
    assert calls.index("a2dismod php7.4") < calls.index("systemctl start apache2.service")
    assert all("openwb2" not in call and "php -f" not in call for call in calls)


@pytest.mark.parametrize("entry", [None, "php.load", "php7.4.load"])
def test_missing_recognized_modules_prints_diagnostics_without_changes(appliance, entry):
    enabled_dir = appliance / "apache/mods-enabled"
    for module in enabled_dir.glob("*.load"):
        module.unlink()
    if entry == "php.load":
        (enabled_dir / entry).touch()
    elif entry:
        (enabled_dir / entry).symlink_to("../mods-available/missing-php.load")
    result = invoke(appliance, "disable", "--debug")
    assert result.returncode != 0
    assert "DIAGNOSTIC: recognized enabled PHP modules: (none)" in result.stderr
    assert "mods-enabled PHP entries" in result.stderr
    assert "mods-available PHP entries" in result.stderr
    assert "Apache PHP/CGI module report" in result.stderr
    assert "HTTP 403 alone does not prove mod_php is unloaded" in result.stderr
    assert "failed during detecting PHP modules and rollback state" in result.stderr
    assert "configuration was not changed by this run" in result.stderr
    if entry:
        assert entry in result.stderr
    if entry == "php.load":
        assert "php_module (shared)" in result.stderr
    if entry == "php7.4.load":
        assert "../mods-available/missing-php.load" in result.stderr
    assert not (appliance / "state/state").exists()
    assert "systemctl stop" not in (appliance / "commands").read_text()


def test_existing_guard_is_reported_when_php_is_already_disabled(appliance):
    assert invoke(appliance, "disable").returncode == 0
    # Reproduce blocking without this script's saved state; never invent rollback modules.
    (appliance / "state/state").unlink()
    result = invoke(appliance, "disable", "--debug")
    assert result.returncode != 0
    assert "PHP deny guard is already enabled" in result.stdout
    assert "HTTP 403 may be due to this existing rule" in result.stdout
    assert "No enabled Debian mod_php module found" in result.stderr


def test_missing_modules_without_debug_keeps_error_and_suggests_debug(appliance):
    for module in (appliance / "apache/mods-enabled").glob("*.load"):
        module.unlink()
    result = invoke(appliance, "disable")
    assert result.returncode != 0
    assert "No enabled Debian mod_php module found" in result.stderr
    assert "Rerun with --debug" in result.stderr
    assert "DIAGNOSTIC:" not in result.stderr


@pytest.mark.parametrize("arguments", [("--debug", "disable"), ("disable", "--debug")])
def test_debug_flag_before_or_after_mode(appliance, arguments):
    result = invoke(appliance, *arguments)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "INFO: checking Apache configuration" in result.stdout
    assert "INFO: recognized enabled PHP modules:" in result.stdout
    assert "CONFIRMED:" in result.stdout


@pytest.mark.parametrize("arguments", [("--debug",), ("disable", "enable"), ("disable", "--unknown")])
def test_invalid_arguments_do_not_change_configuration(appliance, arguments):
    result = invoke(appliance, *arguments)
    assert result.returncode != 0
    assert "Usage:" in result.stdout
    assert not (appliance / "commands").exists()


@pytest.mark.parametrize("sites, expected_urls", [
    (["000-default"], ["http://127.0.0.1"]),
    (["apache-openwb-ssl", "apache-redirect-ssl"], ["https://127.0.0.1"]),
    (["localhost"], ["http://127.0.0.1:81"]),
    (["000-default", "apache-openwb-ssl"], ["http://127.0.0.1", "https://127.0.0.1"]),
])
def test_validates_available_sites_without_requiring_localhost(appliance, sites, expected_urls):
    for site in (appliance / "apache/sites-enabled").glob("*.conf"):
        site.unlink()
    for site in sites:
        (appliance / "apache/sites-enabled" / (site + ".conf")).touch()
    for mode in ("disable", "enable"):
        result = invoke(appliance, mode)
        assert result.returncode == 0, result.stdout + result.stderr
        checks = [line.split(": static")[0] for line in result.stdout.splitlines() if line.startswith("CHECK ")]
        assert checks == ["CHECK " + url for url in expected_urls]
    assert not (appliance / "state/state").exists()


def test_no_standard_validation_site_fails_before_changes(appliance):
    for site in (appliance / "apache/sites-enabled").glob("*.conf"):
        site.unlink()
    # A redirect-only listener cannot validate static serving or PHP denial.
    (appliance / "apache/sites-enabled/apache-redirect-ssl.conf").touch()
    result = invoke(appliance, "disable")
    assert result.returncode != 0
    assert "No standard openWB website enabled" in result.stderr
    assert "systemctl stop" not in (appliance / "commands").read_text()
    assert not (appliance / "state/state").exists()
    assert (appliance / "active").exists()


@pytest.mark.parametrize("failure", ["fail-http", "alternate", "fail-config", "fail-stop", "fail-guard"])
def test_failures_attempt_containment(appliance, failure):
    (appliance / failure).touch()
    result = invoke(appliance, "disable")
    assert result.returncode != 0
    assert "CONFIRMED:" not in result.stdout
    assert "NOT confirmed" in result.stderr
    assert (appliance / "state/state").exists()
    if failure in {"fail-stop", "fail-guard"}:
        assert "cleanup unconfirmed" in result.stderr
    else:
        assert "Apache stopped" in result.stderr
        assert not (appliance / "active").exists()
    calls = (appliance / "commands").read_text()
    assert "systemctl stop apache2.service" in calls
    assert "a2enconf disable-web-php" in calls
    assert "failed during" in result.stderr
    if failure == "fail-http":
        assert "checking static website and PHP response at http://127.0.0.1:81" in result.stderr


def test_failed_enable_keeps_state_and_cleans_probe(appliance):
    assert invoke(appliance, "disable").returncode == 0
    (appliance / "fail-http").touch()
    assert invoke(appliance, "enable").returncode != 0
    assert (appliance / "state/state").exists()
    assert (appliance / "apache/conf-enabled/disable-web-php.conf").exists()
    assert not (appliance / "active").exists()
    assert not list((appliance / "web").iterdir())


def test_failed_initial_enable_can_be_retried(appliance):
    (appliance / "fail-http").touch()
    assert invoke(appliance, "enable").returncode != 0
    assert (appliance / "state/state").exists()
    assert (appliance / "apache/conf-enabled/disable-web-php.conf").exists()
    (appliance / "fail-http").unlink()
    # The operator deliberately restarts the stopped service before live validation.
    (appliance / "active").touch()
    result = invoke(appliance, "enable")
    assert result.returncode == 0, result.stdout + result.stderr
    assert not (appliance / "state/state").exists()


@pytest.mark.parametrize("mode", ["enable", "disable"])
def test_stopped_service_is_not_started(appliance, mode):
    (appliance / "active").unlink()
    result = invoke(appliance, mode)
    assert result.returncode != 0
    assert "start it explicitly" in result.stderr
    assert "systemctl start" not in (appliance / "commands").read_text()
    assert not (appliance / "state/state").exists()


def test_invalid_saved_state_is_not_executed(appliance):
    assert invoke(appliance, "disable").returncode == 0
    (appliance / "state/state").write_text("true\n$(touch malicious)\n")
    result = invoke(appliance, "enable")
    assert result.returncode != 0
    assert "Invalid saved PHP module" in result.stderr
    assert not (appliance / "malicious").exists()


def test_missing_saved_module_keeps_guard(appliance):
    assert invoke(appliance, "disable").returncode == 0
    (appliance / "apache/mods-available/php7.4.load").unlink()
    result = invoke(appliance, "enable")
    assert result.returncode != 0
    assert "no longer installed" in result.stderr
    assert (appliance / "apache/conf-enabled/disable-web-php.conf").exists()


def test_shared_lock_blocks_configuration_changes(appliance):
    lock_dir = appliance / "lock"
    lock_dir.mkdir()
    lock = lock_dir / "configuration.lock"
    lock.touch()
    with lock.open("r") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        process = subprocess.Popen(["bash", str(appliance / "script.sh"), "disable"],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   env={**os.environ, "ROOT": str(appliance)})
        try:
            with pytest.raises(subprocess.TimeoutExpired):
                process.communicate(timeout=0.2)
            assert not (appliance / "commands").exists()
            fcntl.flock(handle, fcntl.LOCK_UN)
            stdout, stderr = process.communicate(timeout=15)
            assert process.returncode == 0, stdout + stderr
        finally:
            if process.poll() is None:
                process.kill()
                process.communicate()


def test_deny_rule_with_real_apache():
    apache = shutil.which("apache2")
    modules = Path("/usr/lib/apache2/modules")
    if not apache or not (modules / "mod_mpm_event.so").exists():
        pytest.skip("Debian Apache not installed")
    guard = SCRIPT.read_text().split("<<'EOF' || return 1\n", 1)[1].split("\nEOF", 1)[0]
    with tempfile.TemporaryDirectory(prefix="bash-php-apache-") as directory:
        root = Path(directory)
        root.chmod(0o755)
        (root / "index.html").write_text("dashboard")
        (root / "source.php").write_text("<?php secret source")
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
        config = root / "apache.conf"
        config.write_text(
            f'ServerRoot "{root}"\nPidFile "{root}/pid"\nErrorLog "{root}/error.log"\n'
            f'ServerName localhost\nListen 127.0.0.1:{port}\n'
            f'LoadModule mpm_event_module {modules}/mod_mpm_event.so\n'
            f'LoadModule authz_core_module {modules}/mod_authz_core.so\n'
            + ("User www-data\nGroup www-data\n" if os.geteuid() == 0 else "")
            + guard + f'\nDocumentRoot "{root}"\n<Directory "{root}">\nRequire all granted\n</Directory>\n')
        process = subprocess.Popen([apache, "-f", str(config), "-X"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        client = build_opener(ProxyHandler({}))
        url = f"http://127.0.0.1:{port}"
        try:
            for _ in range(100):
                try:
                    with client.open(url + "/index.html", timeout=1) as response:
                        assert response.read() == b"dashboard"
                    break
                except URLError:
                    assert process.poll() is None, process.communicate()
                    time.sleep(0.05)
            else:
                pytest.fail("Apache did not start")
            for suffix in ("php", "PHP", "php7", "phtml", "phar", "phps", "php.txt", "php/path"):
                with pytest.raises(HTTPError) as error:
                    client.open(url + "/source." + suffix, timeout=2)
                assert error.value.code == 403
                assert b"<?php" not in error.value.read()
        finally:
            process.terminate()
            process.communicate(timeout=10)


def test_help_and_invalid_mode():
    assert subprocess.run(["bash", str(SCRIPT), "--help"], capture_output=True).returncode == 0
    assert subprocess.run(["bash", str(SCRIPT), "invalid"], capture_output=True).returncode == 1
