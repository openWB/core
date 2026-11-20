#!/bin/bash
OPENWBBASEDIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

# Old updaters may already have checked out trixie-next. Recover before any
# virtualenv, package, service, network or boot-configuration migration runs.
guardFailureState() {
	# Independent of the sourced helper, so missing helpers are covered too.
	python3 - "$OPENWBBASEDIR" "$1" <<'PY'
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time

base = Path(sys.argv[1])
action = sys.argv[2]
state_file = base / "data/log/os-update-guard.json"
boot_id = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
fingerprint = hashlib.sha256()
for name in ("runs/atreboot.sh", "runs/update_self.sh", "runs/os_update_guard.sh", "packages/main.py"):
    path = base / name
    fingerprint.update(name.encode())
    fingerprint.update(path.read_bytes() if path.is_file() else b"missing")
key = boot_id + ":" + fingerprint.hexdigest()
def load_record():
    try:
        item = json.loads(state_file.read_text())
        if (not isinstance(item, dict) or not isinstance(item.get("key"), str)
                or type(item.get("failed_at")) not in (int, float)
                or not math.isfinite(item["failed_at"]) or item["failed_at"] < 0
                or type(item.get("timestamp")) is not int
                or type(item.get("sent")) is not bool
                or not isinstance(item.get("topic"), str)
                or not re.fullmatch(r"openWB/system/messages/[0-9]+", item["topic"])):
            return {}
        return item
    except (OSError, ValueError):
        return {}

record = load_record()
same_failure = record.get("key") == key
if action == "retry":
    # Service restarts must not immediately repeat a failed Git fetch. A
    # direct user-requested update_self.sh call is not subject to this delay.
    sys.exit(1 if same_failure and time.monotonic() - record.get("failed_at", 0) < 300 else 0)

message = (
    "Der automatische Wechsel zum kompatiblen Release ist fehlgeschlagen. "
    "openWB 2.5.x wurde auf diesem Betriebssystem nicht gestartet. "
    "Bitte Update-Log prüfen."
)
items = [
    ("openWB/set/system/update_in_progress", False),
    ("openWB/system/update_in_progress", False),
]
def publish(topic, payload):
    try:
        subprocess.run(
            ["mosquitto_pub", "-h", "127.0.0.1", "-p", "1886",
             "-t", topic, "-q", "1", "-r", "-s"],
            input=json.dumps(payload), universal_newlines=True,
            timeout=3, check=True,
        )
        return True
    except Exception:
        return False

for topic, payload in items:
    publish(topic, payload)

# Keep one event ID per failure/boot/code version. QoS1 retries replay that
# same retained event; acknowledged/dismissed events are not recreated.
try:
    state_file.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(state_file) + ".lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        record = load_record()
        if record.get("key") != key:
            record = {"key": key, "failed_at": time.monotonic(),
                      "topic": "openWB/system/messages/" + str(int(time.time() * 1000)),
                      "timestamp": int(time.time()), "sent": False}
        elif time.monotonic() - record["failed_at"] >= 300:
            record["failed_at"] = time.monotonic()

        def save():
            fd, name = tempfile.mkstemp(dir=state_file.parent, prefix=".os-update-guard-")
            try:
                with os.fdopen(fd, "w") as stream:
                    json.dump(record, stream)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(name, state_file)
            finally:
                if os.path.exists(name):
                    os.unlink(name)

        save()
        if not record["sent"]:
            payload = {"source": "command", "type": "danger", "message": message,
                       "timestamp": record["timestamp"]}
            if time.time() - record["timestamp"] > 60:
                payload["message"] = "Verzögert zugestellt: " + message
            if publish(record["topic"], payload):
                record["sent"] = True
                save()
except (OSError, ValueError, KeyError):
    print("Cannot persist OS guard failure status; application startup remains blocked.", file=sys.stderr)
PY
}
guardFailure() {
	guardFailureState report || true
	exit 1
}
source "$OPENWBBASEDIR/runs/os_update_guard.sh" || guardFailure
requiresSystemUpdate
guardStatus=$?
case "$guardStatus" in
	0)
		guardFailureState retry || guardFailure
		bash "$OPENWBBASEDIR/runs/update_self.sh" "trixie-next" || guardFailure
		# Recovery either requested a reboot or failed. Never enter the new
		# OS startup migrations from this already-open copy of atreboot.sh.
		exit 0
		;;
	1) ;;
	*) echo "Cannot read OS identity; refusing startup changes." >&2; guardFailure ;;
esac

hasInet=0

# setup log file
LOGFILE="${OPENWBBASEDIR}/ramdisk/main.log"
touch "$LOGFILE"
chmod 666 "$LOGFILE"

{
	versionMatch() {
		file=$1
		target=$2
		currentVersion=$(grep -o "openwb-version:[0-9]\+" "$file" | grep -o "[0-9]\+$")
		installedVersion=$(sudo grep -o "openwb-version:[0-9]\+" "$target" | grep -o "[0-9]\+$")
		if ((currentVersion == installedVersion)); then
			return 0
		else
			return 1
		fi
	}

	mkdir -p "${OPENWBBASEDIR}/.venvs"
	if [[ ! -e "${OPENWBBASEDIR}/.venvs/.migrated" && ! -f "${OPENWBBASEDIR}/.venv/.openwb-ready" && -e /etc/systemd/system/openwb2.service ]]; then
		touch "${OPENWBBASEDIR}/.venvs/.legacy"
	fi

	# check for pending factory reset
	if [[ -f "${OPENWBBASEDIR}/data/restore/factory_reset" ]]; then
		echo "pending factory_reset detected, executing factory_reset"
		# remove flag to prevent a boot loop on failure
		rm "${OPENWBBASEDIR}/data/restore/factory_reset"
		sudo "${OPENWBBASEDIR}/runs/factory_reset.sh" "clearall"
	else
		echo "no factory reset pending, normal startup"
	fi

	echo "atreboot.sh started"
	if [[ -f "${OPENWBBASEDIR}/ramdisk/bootdone" ]]; then
		mosquitto_pub -p 1886 -t "openWB/system/boot_done" -r -m 'false'
		rm "${OPENWBBASEDIR}/ramdisk/bootdone"
	fi
	(
		echo "watchdog for atreboot.sh on pid $$ started, waiting for 900s"
		sleep 900
		if sudo kill "$$"; then
			echo "killed stalled atreboot.sh!"
			mosquitto_pub -p 1886 -t "openWB/system/update_in_progress" -r -m 'false'
			mosquitto_pub -p 1886 -t "openWB/system/boot_done" -r -m 'true'
			# mosquitto_pub -p 1886 -t "openWB/system/reloadDisplay" -m "1"
			touch "${OPENWBBASEDIR}/ramdisk/bootdone"
		else
			echo "seems like atreboot.sh finished normally"
		fi
	) &

	boot_config_source="${OPENWBBASEDIR}/data/config/boot_config.txt"
	boot_config_target="/boot/config.txt"
	echo "checking init in $boot_config_target..."
	if versionMatch "$boot_config_source" "$boot_config_target"; then
		echo "already up to date"
	else
		echo "openwb section not found or outdated"
		pattern_begin=$(grep -m 1 '#' "$boot_config_source")
		pattern_end=$(grep '#' "$boot_config_source" | tail -n 1)
		sudo sed -i "/$pattern_begin/,/$pattern_end/d" "$boot_config_target"
		echo "adding init to $boot_config_target..."
		sudo tee -a "$boot_config_target" <"$boot_config_source" >/dev/null
		echo "done"
		sudo reboot now
	fi

	# check group membership
	echo "Group membership..."
	# TODO: remove sudo group membership if possible
	for group in "input" "dialout" "gpio" "sudo" "video"; do
		if ! groups openwb | grep --quiet "$group"; then
			if getent group | cut -d: -f1 | grep --quiet "$group"; then
				sudo usermod -G "$group" -a openwb
				echo "added openwb to group '$group'"
			else
				echo "required group '$group' missing on this system!"
			fi
		fi
	done
	echo -n "Final group membership: "
	groups openwb

	# allow apache to restart some services
	echo "Apache service restart permissions..."
	if versionMatch "${OPENWBBASEDIR}/data/config/sudoers/apache2" "/etc/sudoers.d/apache2"; then
		echo "apache2 sudoers already up to date"
	else
		echo "updating apache2 sudoers"
		sudo cp "${OPENWBBASEDIR}/data/config/sudoers/apache2" "/etc/sudoers.d/apache2"
		sudo chmod 440 /etc/sudoers.d/apache2
	fi

	# network setup
	echo "Network..."
	if "${OPENWBBASEDIR}/runs/setup_network.sh"; then
		hasInet=1
		echo "network setup done"
	else
		hasInet=0
		echo "#### network setup failed!"
		echo "#### unable to update dependencies and version information"
		echo "#### continue anyway..."
	fi

	# tune apt configuration and install required packages
	if [ -d "/etc/apt/apt.conf.d" ]; then
		if versionMatch "${OPENWBBASEDIR}/data/config/apt/99openwb" "/etc/apt/apt.conf.d/99openwb"; then
			echo "apt configuration already up to date"
		else
			echo "updating apt configuration"
			sudo cp "${OPENWBBASEDIR}/data/config/apt/99openwb" "/etc/apt/apt.conf.d/99openwb"
		fi
	else
		echo "path '/etc/apt/apt.conf.d' is missing! unsupported system!"
	fi
	if ((hasInet == 1)); then
		if ! "${OPENWBBASEDIR}/runs/install_packages.sh"; then
			echo "System package installation failed; prerequisites may be missing!" >&2
		fi
	else
		echo "no internet connection, skipping package installation"
	fi

	if ! bash "${OPENWBBASEDIR}/runs/setup_python_venv.sh" "$OPENWBBASEDIR" 0 --boot-cleanup "$(cat /proc/sys/kernel/random/boot_id)"; then
		echo "Python environment boot cleanup failed" >&2
	fi
	venv_status=0
	bash "${OPENWBBASEDIR}/runs/setup_python_venv.sh" "$OPENWBBASEDIR" "$hasInet" || venv_status=$?
	if ((venv_status != 0 && venv_status != 10)); then
		echo "Python environment setup failed; retaining the previous environment" >&2
		message="Bei der Installation der benötigten Python-Bibliotheken ist ein Fehler aufgetreten! Bitte die Logdateien prüfen."
		payload=$(printf '{"source": "system", "type": "danger", "message": "%s", "timestamp": %d}' "$message" "$(date +"%s")")
		mosquitto_pub -p 1886 -t "openWB/system/messages/$(date +"%s%3N")" -r -m "$payload"
	fi

	# check for openwb cron jobs
	if versionMatch "${OPENWBBASEDIR}/data/config/openwb.cron" "/etc/cron.d/openwb"; then
		echo "openwb.cron already up to date"
	else
		echo "updating openwb.cron"
		sudo cp "${OPENWBBASEDIR}/data/config/openwb.cron" "/etc/cron.d/openwb"
	fi

	# check for openwb2 service definition
	if find /etc/systemd/system/ -maxdepth 1 -name openwb2.service -type l | grep -q "."; then
		echo "openwb2.service definition is already a symlink"
	else
		sudo ln -s "${OPENWBBASEDIR}/data/config/openwb2.service" /etc/systemd/system/openwb2.service
		sudo systemctl daemon-reload
		echo "openwb2.service definition updated. rebooting..."
		sudo reboot now &
	fi

	# check for openwb-simpleAPI service definition
	if find /etc/systemd/system/ -maxdepth 1 -name openwb-simpleAPI.service -type l | grep -q "."; then
		echo "openwb-simpleAPI.service definition is already a symlink"
	else
		sudo ln -s "${OPENWBBASEDIR}/data/config/openwb-simpleAPI.service" /etc/systemd/system/openwb-simpleAPI.service
		sudo systemctl daemon-reload
		sudo systemctl enable openwb-simpleAPI
		sudo systemctl restart openwb-simpleAPI
		echo "openwb-simpleAPI.service definition updated."
	fi

	# check for remote support service definition
	if [ ! -f "/etc/systemd/system/openwbRemoteSupport.service" ]; then
		echo "openwbRemoteSupport service missing, installing service"
		sudo cp "${OPENWBBASEDIR}/data/config/openwbRemoteSupport.service" "/etc/systemd/system/openwbRemoteSupport.service"
		sudo systemctl daemon-reload
		sudo systemctl enable openwbRemoteSupport
		sudo systemctl start openwbRemoteSupport
	else
		if versionMatch "${OPENWBBASEDIR}/data/config/openwbRemoteSupport.service" "/etc/systemd/system/openwbRemoteSupport.service"; then
			echo "openwbRemoteSupport.service already up to date"
		else
			echo "updating openwbRemoteSupport.service"
			sudo cp "${OPENWBBASEDIR}/data/config/openwbRemoteSupport.service" "/etc/systemd/system/openwbRemoteSupport.service"
			sudo systemctl daemon-reload
			sudo systemctl enable openwbRemoteSupport
			sudo systemctl restart openwbRemoteSupport
		fi
	fi

	unit_hash=$(sha256sum "${OPENWBBASEDIR}/data/config/openwb2.service" "${OPENWBBASEDIR}/data/config/openwb-simpleAPI.service" "${OPENWBBASEDIR}/data/config/openwbRemoteSupport.service" | sha256sum | cut -d ' ' -f 1)
	previous_unit_hash=$(cat "${OPENWBBASEDIR}/.venvs/.unit-hash" 2>/dev/null || true)
	if [[ "$unit_hash" != "$previous_unit_hash" ]]; then
		sudo systemctl daemon-reload
	fi
	if ((venv_status == 10)) || [[ "$unit_hash" != "$previous_unit_hash" ]]; then
		if sudo systemd-run --unit="openwb-python-restart-$$" --collect /bin/bash -c \
			'tail --pid="$1" -f /dev/null; systemctl reset-failed openwb2.service openwb-simpleAPI.service openwbRemoteSupport.service; systemctl restart openwb2.service openwb-simpleAPI.service openwbRemoteSupport.service || rm -f "$2"' \
			openwb-python-restart "$$" "${OPENWBBASEDIR}/.venvs/.unit-hash"; then
			printf '%s\n' "$unit_hash" > "${OPENWBBASEDIR}/.venvs/.unit-hash"
		else
			echo "Failed to schedule Python service restart" >&2
		fi
	fi

	# check for pending restore
	if [[ -f "${OPENWBBASEDIR}/data/restore/run_on_boot" ]]; then
		echo "pending restore detected"
		# remove flag to prevent a boot loop on failure
		rm "${OPENWBBASEDIR}/data/restore/run_on_boot"
		"${OPENWBBASEDIR}/runs/restore.sh"
		# restore.sh will reboot if successful
	else
		echo "no restore pending, normal startup"
	fi

	# clean python cache
	echo "cleaning obsolete python cache folders..."
	"$OPENWBBASEDIR/runs/cleanPythonCache.sh"

	# detect connected displays
	displayDetected="false"
	for connector in /sys/class/drm/card*-*; do
		if [[ -f "$connector/status" && $(cat "$connector/status") == connected ]]; then
			echo "Display connected on: $connector"
			displayDetected="true"
			break
		fi
	done
	echo "displayDetected: $displayDetected"
	forceDisplaySetup=0
	if displayDetected_old=$(mosquitto_sub -p 1886 -t "openWB/optional/int_display/detected" -C 1 -W 1); then
		echo "previous displayDetected value: $displayDetected_old"
		if [[ $displayDetected_old != "$displayDetected" ]]; then
			echo "displayDetected value changed, publishing new value"
			mosquitto_pub -p 1886 -t "openWB/optional/int_display/detected" -r -m "$displayDetected"
		else
			echo "no change in displayDetected value, skipping publish"
		fi
	else
		echo "no previous displayDetected value found, assuming initial boot"
		echo "update of display settings forced"
		forceDisplaySetup=1
		mosquitto_pub -p 1886 -t "openWB/optional/int_display/detected" -r -m "$displayDetected"
		mosquitto_pub -p 1886 -t "openWB/optional/int_display/active" -r -m "true"
	fi

	# display setup
	echo "display setup..."
	displaySetupModified=0
	if [ ! -d "/home/openwb/.config/lxsession/LXDE" ]; then
		mkdir --parents "/home/openwb/.config/lxsession/LXDE"
	fi
	if versionMatch "${OPENWBBASEDIR}/data/config/display/lightdm-autologin-greeter.conf" "/etc/lightdm/lightdm.conf.d/lightdm-autologin-greeter.conf"; then
		echo "autologin configured"
	else
		echo "updating autologin"
		sudo cp "${OPENWBBASEDIR}/data/config/display/lightdm-autologin-greeter.conf" "/etc/lightdm/lightdm.conf.d/lightdm-autologin-greeter.conf"
		displaySetupModified=1
	fi
	if versionMatch "${OPENWBBASEDIR}/data/config/display/lightdm-hide-mouse-cursor.conf" "/etc/lightdm/lightdm.conf.d/lightdm-hide-mouse-cursor.conf"; then
		echo "mouse cursor configured"
	else
		echo "updating mouse cursor configuration"
		sudo cp "${OPENWBBASEDIR}/data/config/display/lightdm-hide-mouse-cursor.conf" "/etc/lightdm/lightdm.conf.d/lightdm-hide-mouse-cursor.conf"
		displaySetupModified=1
	fi
	if versionMatch "${OPENWBBASEDIR}/data/config/display/lxdeautostart" "/home/openwb/.config/lxsession/LXDE/autostart"; then
		echo "lxde session autostart already configured"
	else
		echo "updating lxde session autostart"
		cp "${OPENWBBASEDIR}/data/config/display/lxdeautostart" "/home/openwb/.config/lxsession/LXDE/autostart"
		displaySetupModified=1
	fi
	if ((displaySetupModified == 1)) || ((forceDisplaySetup == 1)); then
		"${OPENWBBASEDIR}/runs/update_local_display.sh" $forceDisplaySetup
	fi

	# check apache configuration
	"${OPENWBBASEDIR}/runs/setup_apache2.sh"

	# check for mosquitto configuration
	"${OPENWBBASEDIR}/runs/setup_mosquitto.sh" 1

	# check for home configuration
	if [[ ! -f "/home/openwb/configuration.json" ]]; then
		sudo cp -a "${OPENWBBASEDIR}/data/config/configuration.json" "/home/openwb/configuration.json"
	fi

	# collect some hardware info
	"${OPENWBBASEDIR}/runs/uuid.sh"

	# update current published versions
	if ((hasInet == 1)); then
		echo "load versions..."
		"$OPENWBBASEDIR/runs/update_available_versions.sh"
	else
		echo "no internet connection, updating versions from local git data"
		"$OPENWBBASEDIR/runs/update_available_versions.sh" --no-fetch
	fi

	# set restore dir permissions to allow file upload for apache
	sudo chgrp -R www-data "${OPENWBBASEDIR}/data/restore/." "${OPENWBBASEDIR}/data/data_migration/."
	sudo chmod -R g+w "${OPENWBBASEDIR}/data/restore/." "${OPENWBBASEDIR}/data/data_migration/."

	# cleanup some folders
	folder="${OPENWBBASEDIR}/data/data_migration/var"
	if [ -d "$folder" ]; then
		echo "deleting temporary data migration folder"
		rm -R "$folder"
	fi
	files=("${OPENWBBASEDIR}/data/data_migration/data_migration.tar" "${OPENWBBASEDIR}/data/data_migration/data_migration.tar.gz")
	for file in "${files[@]}"; do
		if [ -f "$file" ]; then
			echo "deleting temporary data migration file '$file'"
			rm "$file"
		fi
	done

	# all done, remove boot and update status
	echo "$(date +"%Y-%m-%d %H:%M:%S:")" "boot done :-)"
	mosquitto_pub -p 1886 -t "openWB/system/update_in_progress" -r -m 'false'
	mosquitto_pub -p 1886 -t "openWB/system/reloadDisplay" -m "1"
} >>"$LOGFILE" 2>&1
