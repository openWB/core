#!/bin/bash
OPENWBBASEDIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

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
		echo "new configuration active after next boot"
	fi

	# check group membership
	echo "Group membership..."
	for group in "input" "dialout"; do
		if ! groups openwb | grep --quiet "$group"; then
			sudo usermod -G "$group" -a openwb
			echo "added openwb to group '$group'"
		fi
	done
	echo -n "Final group membership: "
	groups openwb

	# network setup
	echo "Network..."
	"${OPENWBBASEDIR}/runs/setup_network.sh"

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
	"${OPENWBBASEDIR}/runs/install_packages.sh"

	# check for openwb cron jobs
	if versionMatch "${OPENWBBASEDIR}/data/config/openwb.cron" "/etc/cron.d/openwb"; then
		echo "openwb.cron already up to date"
	else
		echo "updating openwb.cron"
		sudo cp "${OPENWBBASEDIR}/data/config/openwb.cron" "/etc/cron.d/openwb"
	fi

	# check for openwb2 service definition
	if versionMatch "${OPENWBBASEDIR}/data/config/openwb2.service" "/etc/systemd/system/openwb2.service"; then
		echo "openwb2.service already up to date"
	else
		echo "updating openwb2.service"
		sudo cp "${OPENWBBASEDIR}/data/config/openwb2.service" "/etc/systemd/system/openwb2.service"
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
		echo "pending restore detected, executing restore"
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

	# check for apache configuration
	echo "apache default site..."
	restartService=0
	if versionMatch "${OPENWBBASEDIR}/data/config/000-default.conf" "/etc/apache2/sites-available/000-default.conf"; then
		echo "...ok"
	else
		sudo cp "${OPENWBBASEDIR}/data/config/000-default.conf" "/etc/apache2/sites-available/"
		restartService=1
		echo "...updated"
	fi
	echo "checking required apache modules..."
	if sudo a2query -m headers; then
		echo "headers already enabled"
	else
		echo "headers currently disabled; enabling module"
		sudo a2enmod headers
		restartService=1
	fi
	if sudo a2query -m ssl; then
		echo "ssl already enabled"
	else
		echo "ssl currently disabled; enabling module"
		sudo a2enmod ssl
		restartService=1
	fi
	if sudo a2query -m proxy_wstunnel; then
		echo "proxy_wstunnel already enabled"
	else
		echo "proxy_wstunnel currently disabled; enabling module"
		sudo a2enmod proxy_wstunnel
		restartService=1
	fi
	if ! versionMatch "${OPENWBBASEDIR}/data/config/apache-openwb-ssl.conf" "/etc/apache2/sites-available/apache-openwb-ssl.conf"; then
		echo "installing ssl site configuration"
		sudo a2dissite default-ssl
		sudo cp "${OPENWBBASEDIR}/data/config/apache-openwb-ssl.conf" "/etc/apache2/sites-available/"
		sudo a2ensite apache-openwb-ssl
		restartService=1
	fi
	if ((restartService == 1)); then
		echo -n "restarting apache..."
		sudo systemctl restart apache2
		echo "done"
	fi

	# check for mosquitto configuration
	echo "check mosquitto installation..."
	restartService=0
	if versionMatch "${OPENWBBASEDIR}/data/config/mosquitto.conf" "/etc/mosquitto/mosquitto.conf"; then
		echo "mosquitto.conf already up to date"
	else
		echo "updating mosquitto.conf"
		sudo cp "${OPENWBBASEDIR}/data/config/mosquitto.conf" "/etc/mosquitto/mosquitto.conf"
		restartService=1
	fi
	if versionMatch "${OPENWBBASEDIR}/data/config/openwb.conf" "/etc/mosquitto/conf.d/openwb.conf"; then
		echo "mosquitto openwb.conf already up to date"
	else
		echo "updating mosquitto openwb.conf"
		sudo cp "${OPENWBBASEDIR}/data/config/openwb.conf" "/etc/mosquitto/conf.d/openwb.conf"
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
		sudo systemctl stop mosquitto
		sleep 2
		sudo systemctl start mosquitto
		echo "done"
	fi

	#check for mosquitto_local instance
	restartService=0
	if versionMatch "${OPENWBBASEDIR}/data/config/mosquitto_local.conf" "/etc/mosquitto/mosquitto_local.conf"; then
		echo "mosquitto_local.conf already up to date"
	else
		echo "updating mosquitto_local.conf"
		sudo cp -a "${OPENWBBASEDIR}/data/config/mosquitto_local.conf" "/etc/mosquitto/mosquitto_local.conf"
		restartService=1
	fi
	if versionMatch "${OPENWBBASEDIR}/data/config/openwb_local.conf" "/etc/mosquitto/conf_local.d/openwb_local.conf"; then
		echo "mosquitto openwb_local.conf already up to date"
	else
		echo "updating mosquitto openwb_local.conf"
		sudo cp -a "${OPENWBBASEDIR}/data/config/openwb_local.conf" "/etc/mosquitto/conf_local.d/"
		restartService=1
	fi
	if ((restartService == 1)); then
		echo -n "restarting mosquitto_local service..."
		sudo systemctl stop mosquitto_local
		sleep 2
		sudo systemctl start mosquitto_local
		echo "done"
	fi
	echo "mosquitto done"

	# check for python dependencies
	echo "install required python packages with 'pip3'..."
	pip3 install -r "${OPENWBBASEDIR}/requirements.txt"
	echo "done"

	# collect some hardware info
	"${OPENWBBASEDIR}/runs/uuid.sh"

	# update current published versions
	echo "load versions..."
	"$OPENWBBASEDIR/runs/update_available_versions.sh"
	# # and record the current commit details
	# commitId=$(git -C "${OPENWBBASEDIR}/" log --format="%h" -n 1)
	# echo "$commitId" > "${OPENWBBASEDIR}/ramdisk/currentCommitHash"
	# git -C "${OPENWBBASEDIR}/" branch -a --contains "$commitId" | perl -nle 'm|.*origin/(.+).*|; print $1' | uniq | xargs > "${OPENWBBASEDIR}/ramdisk/currentCommitBranches"

	# set restore dir permissions to allow file upload for apache
	sudo chgrp www-data "${OPENWBBASEDIR}/data/restore" "${OPENWBBASEDIR}/data/restore/"* "${OPENWBBASEDIR}/data/data_migration" "${OPENWBBASEDIR}/data/data_migration/"*
	sudo chmod g+w "${OPENWBBASEDIR}/data/restore" "${OPENWBBASEDIR}/data/restore/"* "${OPENWBBASEDIR}/data/data_migration" "${OPENWBBASEDIR}/data/data_migration/"*

	# all done, remove boot and update status
	echo "$(date +"%Y-%m-%d %H:%M:%S:")" "boot done :-)"
	mosquitto_pub -p 1886 -t "openWB/system/update_in_progress" -r -m 'false'
	mosquitto_pub -p 1886 -t "openWB/system/reloadDisplay" -m "1"
} >>"$LOGFILE" 2>&1
