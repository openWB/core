#!/bin/bash
OPENWBBASEDIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
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
		installedVersion=$(grep -o "openwb-version:[0-9]\+" "$target" | grep -o "[0-9]\+$")
		# echo "$currentVersion == $installedVersion ?"
		if ((currentVersion == installedVersion)); then
			return 0
		else
			return 1
		fi
	}

	waitForServiceStop() {
		# this function waits for a service to stop and kills the process if it takes too long
		# this is necessary at least for mosquitto, as the service is stopped, but the process is still running
		service=$1
		pattern=$2
		timeout=$3

		counter=0
		sudo systemctl stop "$service"
		while pgrep --full "$pattern" >/dev/null && ((counter < timeout)); do
			echo "process '$pattern' still running after ${counter}s, waiting..."
			sleep 1
			((counter++))
		done
		if ((counter >= timeout)); then
			echo "process '$pattern' still running after ${timeout}s, killing process"
			sudo pkill --full "$pattern" --signal 9
			sleep 2
			# if the process was killed, the service is in "active (exited)" state
			# so we need to trigger a stop here to be able to start it again
			sudo systemctl stop "$service"
		fi
	}

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
		if ((hasInet == 1)); then
			"${OPENWBBASEDIR}/runs/restore.sh"
			# restore.sh will reboot if successful
		else
			echo "no internet connection, restore not possible, skipping"
		fi
	else
		echo "no restore pending, normal startup"
	fi

	# clean python cache
	echo "cleaning obsolete python cache folders..."
	"$OPENWBBASEDIR/runs/cleanPythonCache.sh"

	# detect connected displays
	# set default to "true" as fallback if "tvservice" is missing
	displayDetected="true"
	if which tvservice >/dev/null; then
		echo "detected 'tvservice', query for connected displays"
		output=$(tvservice -l)
		echo "$output"
		if [[ ! $output =~ "HDMI" ]] && [[ ! $output =~ "LCD" ]]; then
			echo "no display detected"
			displayDetected="false"
		else
			echo "detected HDMI or LCD display(s)"
		fi
	else
		echo "'tvservice' not found, assuming a display is present"
	fi
	echo "displayDetected: $displayDetected"
	mosquitto_pub -p 1886 -t "openWB/optional/int_display/detected" -r -m "$displayDetected"

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
	if ((displaySetupModified == 1)); then
		"${OPENWBBASEDIR}/runs/update_local_display.sh"
	fi

	# check apache configuration
	"${OPENWBBASEDIR}/runs/setup_apache2.sh"

	# check for mosquitto configuration
	echo "check mosquitto installation..."
	restartService=0
	if versionMatch "${OPENWBBASEDIR}/data/config/mosquitto/mosquitto.conf" "/etc/mosquitto/mosquitto.conf"; then
		echo "mosquitto.conf already up to date"
	else
		echo "updating mosquitto.conf"
		sudo cp "${OPENWBBASEDIR}/data/config/mosquitto/mosquitto.conf" "/etc/mosquitto/mosquitto.conf"
		restartService=1
	fi
	if versionMatch "${OPENWBBASEDIR}/data/config/mosquitto/openwb.conf" "/etc/mosquitto/conf.d/openwb.conf"; then
		echo "mosquitto openwb.conf already up to date"
	else
		echo "updating mosquitto openwb.conf"
		sudo cp "${OPENWBBASEDIR}/data/config/mosquitto/openwb.conf" "/etc/mosquitto/conf.d/openwb.conf"
		restartService=1
	fi
	if versionMatch "${OPENWBBASEDIR}/data/config/mosquitto/mosquitto.acl" "/etc/mosquitto/mosquitto.acl"; then
		echo "mosquitto acl already up to date"
	else
		echo "updating mosquitto acl"
		sudo cp "${OPENWBBASEDIR}/data/config/mosquitto/mosquitto.acl" "/etc/mosquitto/mosquitto.acl"
		restartService=1
	fi
	if [[ ! -f "/etc/mosquitto/certs/openwb.key" ]]; then
		echo -n "copy ssl certs..."
		sudo cp "/etc/ssl/certs/ssl-cert-snakeoil.pem" "/etc/mosquitto/certs/openwb.pem"
		sudo cp "/etc/ssl/private/ssl-cert-snakeoil.key" "/etc/mosquitto/certs/openwb.key"
		sudo chgrp mosquitto "/etc/mosquitto/certs/openwb.key"
		restartService=1
		echo "done"
	fi
	if ((restartService == 1)); then
		echo -n "restarting mosquitto service..."
		waitForServiceStop "mosquitto" "mosquitto.conf" 10
		sudo systemctl start mosquitto
		echo "done"
	fi

	#check for mosquitto_local instance
	# restartService=0  # if we restart mosquitto, we need to restart mosquitto_local as well
	if versionMatch "${OPENWBBASEDIR}/data/config/mosquitto/mosquitto_local_init" "/etc/init.d/mosquitto_local"; then
		echo "mosquitto_local service definition already up to date"
	else
		echo "updating mosquitto_local service definition"
		sudo cp "${OPENWBBASEDIR}/data/config/mosquitto/mosquitto_local_init" /etc/init.d/mosquitto_local
		sudo chown root:root /etc/init.d/mosquitto_local
		sudo chmod 755 /etc/init.d/mosquitto_local
		sudo systemctl daemon-reload
		sudo systemctl enable mosquitto_local
		restartService=1
	fi
	if versionMatch "${OPENWBBASEDIR}/data/config/mosquitto/mosquitto_local.conf" "/etc/mosquitto/mosquitto_local.conf"; then
		echo "mosquitto_local.conf already up to date"
	else
		echo "updating mosquitto_local.conf"
		sudo cp -a "${OPENWBBASEDIR}/data/config/mosquitto/mosquitto_local.conf" "/etc/mosquitto/mosquitto_local.conf"
		restartService=1
	fi
	if versionMatch "${OPENWBBASEDIR}/data/config/mosquitto/openwb_local.conf" "/etc/mosquitto/conf_local.d/openwb_local.conf"; then
		echo "mosquitto openwb_local.conf already up to date"
	else
		echo "updating mosquitto openwb_local.conf"
		sudo cp -a "${OPENWBBASEDIR}/data/config/mosquitto/openwb_local.conf" "/etc/mosquitto/conf_local.d/"
		restartService=1
	fi
	if ((restartService == 1)); then
		echo -n "restarting mosquitto_local service..."
		waitForServiceStop "mosquitto_local" "mosquitto_local.conf" 10
		sudo systemctl start mosquitto_local
		echo "done"
	fi
	echo "mosquitto done"

	# check for home configuration
	if [[ ! -f "/home/openwb/configuration.json" ]]; then
		sudo cp -a "${OPENWBBASEDIR}/data/config/configuration.json" "/home/openwb/configuration.json"
	fi

	# check for python dependencies
	if ((hasInet == 1)); then
		echo "install required python packages with 'pip3'..."
		if pip3 install --upgrade --only-binary :all: -r "${OPENWBBASEDIR}/requirements.txt"; then
			echo "done"
		else
			echo "failed!"
			message="Bei der Installation der benötigten Python-Bibliotheken ist ein Fehler aufgetreten! Bitte die Logdateien prüfen."
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
