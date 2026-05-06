#!/bin/bash
OPENWBBASEDIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
source "${OPENWBBASEDIR}/runs/platform_detect.sh"
detect_platform
hasInet=0

# setup log file
LOGFILE="${OPENWBBASEDIR}/ramdisk/main.log"
touch "$LOGFILE"
chmod 666 "$LOGFILE"

{
	if ! id -u openwb >/dev/null 2>&1; then
		echo "user 'openwb' missing"
		echo "starting upgrade script..."
		"$OPENWBBASEDIR/runs/upgrade2openwbuser.sh" >>"${OPENWBBASEDIR}/data/log/update.log" 2>&1
	fi

	if [ "$(id -u -n)" != "openwb" ]; then
		echo "Re-running script ${BASH_SOURCE[0]} as user openwb"
		exec sudo -u openwb bash "${BASH_SOURCE[0]}"
		exit
	fi

	# check for rc.local bug
	if grep -Fq "do_expand_rootfs" /etc/rc.local.bak; then
		echo "fixing rc.local bug"
		echo "#!/bin/sh -e" | sudo tee "/etc/rc.local.bak" >"/dev/null"
	else
		echo "rc.local bug not found"
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
			mosquitto_pub -p 1886 -t "openWB/system/reloadDisplay" -m "1"
			touch "${OPENWBBASEDIR}/ramdisk/bootdone"
		else
			echo "seems like atreboot.sh finished normally"
		fi
	) &

	boot_config_source="${OPENWBBASEDIR}/data/config/boot_config.txt"
	boot_config_target="/boot/config.txt"
	if [ "$PLATFORM_IS_RPI" = true ]; then
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
	else
		echo "not a Raspberry Pi, skipping boot config"
	fi

	ramdisk_config_source="${OPENWBBASEDIR}/data/config/ramdisk_config.txt"
	ramdisk_config_target="/etc/fstab"
	echo "checking ramdisk settings in $ramdisk_config_target..."
	if versionMatch "$ramdisk_config_source" "$ramdisk_config_target"; then
		echo "already up to date"
	else
		echo "openwb section not found or outdated"
		# delete old settings with version tag
		pattern_begin=$(grep -m 1 '#' "$ramdisk_config_source")
		pattern_end=$(grep '#' "$ramdisk_config_source" | tail -n 1)
		sudo sed -i "/$pattern_begin/,/$pattern_end/d" "$ramdisk_config_target"
		# check for old settings without version tag
		if grep -o "tmpfs ${OPENWBBASEDIR}/ramdisk" "$ramdisk_config_target"; then
			echo "old setting without version tag found, removing"
			sudo sed -i "\#tmpfs ${OPENWBBASEDIR}/ramdisk#D" "$ramdisk_config_target"
		fi
		# add new settings
		echo "adding ramdisk settings to $ramdisk_config_target..."
		sudo tee -a "$ramdisk_config_target" <"$ramdisk_config_source" >/dev/null
		echo "done"
		echo "rebooting system"
		sudo reboot now &
	fi

	# check group membership
	echo "Group membership..."
	# ToDo: remove sudo group membership if possible
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

	# allow caddy to restart some services
	echo "Caddy service restart permissions..."
	if versionMatch "${OPENWBBASEDIR}/data/config/sudoers/caddy" "/etc/sudoers.d/caddy"; then
		echo "caddy sudoers already up to date"
	else
		echo "updating caddy sudoers"
		sudo cp "${OPENWBBASEDIR}/data/config/sudoers/caddy" "/etc/sudoers.d/caddy"
		sudo chmod 440 /etc/sudoers.d/caddy
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

	# run stack upgrade (Python, Caddy, PHP-FPM, Chrony, etc.)
	# idempotent - only changes what's needed
	echo "Checking for stack upgrades..."
	if ((hasInet == 1)); then
		sudo "${OPENWBBASEDIR}/runs/upgrade_stack.sh"
	else
		echo "no internet connection, skipping stack upgrade"
	fi

	# chrony NTP setup
	echo "NTP time synchronization..."
	if versionMatch "${OPENWBBASEDIR}/data/config/chrony/chrony.conf" "/etc/chrony/chrony.conf"; then
		echo "chrony config already up to date"
	else
		echo "configuring chrony NTP..."
		sudo systemctl stop systemd-timesyncd 2>/dev/null || true
		sudo systemctl disable systemd-timesyncd 2>/dev/null || true
		sudo cp "${OPENWBBASEDIR}/data/config/chrony/chrony.conf" /etc/chrony/chrony.conf
		sudo systemctl enable chrony
		sudo systemctl restart chrony
		echo "chrony configured"
	fi

	# MOTD setup
	echo "MOTD setup..."
	sudo cp "${OPENWBBASEDIR}/data/config/profile.d/99-openwb-motd.sh" /etc/profile.d/99-openwb-motd.sh
	sudo chmod 755 /etc/profile.d/99-openwb-motd.sh
	echo "done"

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
		echo "ensuring python virtual environment..."
		ensure_venv "$PLATFORM_VENV"
		"${OPENWBBASEDIR}/runs/install_packages.sh"
	else
		echo "no internet connection, skipping package installation"
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
		if find /etc/systemd/system/ -maxdepth 1 -name openwb2.service -type f | grep -q "."; then
			echo "openwb2.service definition is a regular file, deleting file"
			sudo rm "/etc/systemd/system/openwb2.service"
		fi
		sudo ln -s "${OPENWBBASEDIR}/data/config/openwb2.service" /etc/systemd/system/openwb2.service
		sudo systemctl daemon-reload
		echo "openwb2.service definition updated. rebooting..."
		sudo reboot now &
	fi

	# check for openwb-simpleAPI service definition
	if find /etc/systemd/system/ -maxdepth 1 -name openwb-simpleAPI.service -type l | grep -q "."; then
		echo "openwb-simpleAPI.service definition is already a symlink"
	else
		if find /etc/systemd/system/ -maxdepth 1 -name openwb-simpleAPI.service -type f | grep -q "."; then
			echo "openwb-simpleAPI.service definition is a regular file, deleting file"
			sudo rm "/etc/systemd/system/openwb-simpleAPI.service"
		fi
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
	# set default to "true" as fallback if "tvservice" is missing
	displayDetected="true"
	if [ "$PLATFORM_IS_RPI" = true ] && which tvservice >/dev/null; then
		echo "detected 'tvservice', query for connected displays"
		output=$(tvservice -l)
		echo "$output"
		if [[ ! $output =~ "HDMI" ]] && [[ ! $output =~ "LCD" ]]; then
			echo "no display detected"
			displayDetected="false"
		else
			echo "detected HDMI or LCD display(s)"
		fi
	elif [ "$PLATFORM_VIRT" != "none" ]; then
		echo "virtualized environment detected, no physical display"
		displayDetected="false"
	else
		echo "no tvservice, assuming a display is present"
	fi
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

	# check caddy configuration
	"${OPENWBBASEDIR}/runs/setup_caddy.sh"

	# check for mosquitto configuration
	"${OPENWBBASEDIR}/runs/setup_mosquitto.sh" 1

	# check for home configuration
	if [[ ! -f "/home/openwb/configuration.json" ]]; then
		sudo cp -a "${OPENWBBASEDIR}/data/config/configuration.json" "/home/openwb/configuration.json"
	fi

	# check for python dependencies
	if ((hasInet == 1)); then
		echo "install required python packages into venv..."
		if $PLATFORM_VENV/bin/python3 -m pip install --only-binary :all: -r "${OPENWBBASEDIR}/requirements.txt"; then
			echo "done"
		else
			echo "failed!"
			message="Bei der Installation der benoetigten Python-Bibliotheken ist ein Fehler aufgetreten! Bitte die Logdateien pruefen."
			payload=$(printf '{"source": "system", "type": "danger", "message": "%s", "timestamp": %d}' "$message" "$(date +"%s")")
			mosquitto_pub -p 1886 -t "openWB/system/messages/$(date +"%s%3N")" -r -m "$payload"
		fi
	else
		echo "no internet connection, skipping python package installation"
	fi

	# collect some hardware info
	"${OPENWBBASEDIR}/runs/uuid.sh"

	# update current published versions
	if ((hasInet == 1)); then
		echo "load versions..."
		"$OPENWBBASEDIR/runs/update_available_versions.sh"
	else
		echo "no internet connection, skipping version update"
	fi

	# set restore dir permissions to allow file upload for caddy
	sudo chgrp -R caddy "${OPENWBBASEDIR}/data/restore/." "${OPENWBBASEDIR}/data/data_migration/."
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
