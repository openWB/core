#!/bin/bash
OPENWBBASEDIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

# setup logfile
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
		echo "starting upgrade skript..."
		"$OPENWBBASEDIR/runs/upgrade2openwbuser.sh" >>"${OPENWBBASEDIR}/data/log/update.log" 2>&1
	fi

	if [ "$(id -u -n)" != "openwb" ]; then
		echo "Re-running script ${BASH_SOURCE[0]} as user openwb"
		exec sudo -u openwb bash "${BASH_SOURCE[0]}"
	fi

	echo "atreboot.sh started"
	if [[ -f "${OPENWBBASEDIR}/ramdisk/bootdone" ]]; then
		rm "${OPENWBBASEDIR}/ramdisk/bootdone"
	fi
	(
		sleep 600
		sudo kill "$$"
	) &

	if versionMatch "${OPENWBBASEDIR}/data/config/openwb.cron" "/etc/cron.d/openwb"; then
		echo "openwb.cron already up to date"
	else
		echo "updating openwb.cron"
		sudo cp "${OPENWBBASEDIR}/data/config/openwb.cron" "/etc/cron.d/openwb"
	fi

	if versionMatch "${OPENWBBASEDIR}/data/config/openwb2.service" "/etc/systemd/system/openwb2.service"; then
		echo "openwb2.service already up to date"
	else
		echo "updating openwb2.service"
		sudo cp "${OPENWBBASEDIR}/data/config/openwb2.service" "/etc/systemd/system/openwb2.service"
		sudo reboot now &
	fi

	# check for pending restore
	if [[ -f "${OPENWBBASEDIR}/data/restore/run_on_boot" ]]; then
		echo "pending restore detected, executing restore"
		# remove flag to prevent a boot loop on failure
		rm "${OPENWBBASEDIR}/data/restore/run_on_boot"
		"${OPENWBBASEDIR}/runs/restore.sh"
		# restore.sh will reboot if successfull
	else
		echo "no restore pending, normal startup"
	fi

	# clean python cache
	echo "cleaning obsolete python cache folders..."
	"$OPENWBBASEDIR/runs/cleanPythonCache.sh"

	# check if display is configured and setup timeout
	# if (( displayaktiv == 1 )); then
	# 	echo "display..."
	# 	if ! grep -Fq "pinch" /home/pi/.config/lxsession/LXDE-pi/autostart
	# 	then
	# 		echo "not found"
	# 		echo "@xscreensaver -no-splash" > /home/pi/.config/lxsession/LXDE-pi/autostart
	# 		echo "@point-rpi" >> /home/pi/.config/lxsession/LXDE-pi/autostart
	# 		echo "@xset s 600" >> /home/pi/.config/lxsession/LXDE-pi/autostart
	# 		echo "@chromium-browser --incognito --disable-pinch --kiosk http://localhost/openWB/web/display/" >> /home/pi/.config/lxsession/LXDE-pi/autostart
	# 	fi
	# 	echo "deleting browser cache"
	# 	rm -rf /home/pi/.cache/chromium
	# fi

	# check for LAN/WLAN connection
	echo "LAN/WLAN..."
	# alpha image restricted to LAN only
	sudo ifconfig eth0:0 192.168.193.250 netmask 255.255.255.0 up

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

	# check for needed packages
	echo "apt packages..."
	# nothing here yet, all in install.sh

	# check for mosquitto configuration
	echo "check mosquitto installation..."
	restartService=0
	# check for mosquitto configuration
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

	# check for other dependencies
	echo "python packages..."
	pip3 install -r "${OPENWBBASEDIR}/requirements.txt"

	# update version
	# echo "version..."
	# uuid=$(</sys/class/net/eth0/address)
	# owbv=$(<"${OPENWBBASEDIR}/web/version")
	# curl --connect-timeout 10 -d "update="$releasetrain$uuid"vers"$owbv"" -H "Content-Type: application/x-www-form-urlencoded" -X POST https://openwb.de/tools/update.php

	# check for slave config and start handler
	# alpha image restricted to standalone installation!
	# if (( isss == 1 )); then
	# 	echo "isss..."
	# 	echo $lastmanagement > ${OPENWBBASEDIR}/ramdisk/issslp2act
	# 	if ps ax |grep -v grep |grep "python3 ${OPENWBBASEDIR}/runs/isss.py" > /dev/null
	# 	then
	# 		sudo kill $(ps aux |grep '[i]sss.py' | awk '{print $2}')
	# 	fi
	# 	python3 ${OPENWBBASEDIR}/runs/isss.py &
	# 	# second IP already set up !
	# 	# ethstate=$(</sys/class/net/eth0/carrier)
	# 	# if (( ethstate == 1 )); then
	# 	# 	sudo ifconfig eth0:0 $virtual_ip_eth0 netmask 255.255.255.0 down
	# 	# else
	# 	# 	sudo ifconfig wlan0:0 $virtual_ip_wlan0 netmask 255.255.255.0 down
	# 	# fi
	# fi

	# check for socket system and start handler
	# alpha image restricted to standalone installation!
	# if [[ "$evsecon" == "buchse" ]] && [[ "$isss" == "0" ]]; then
	# 	echo "socket..."
	# 	# ppbuchse is used in issss.py to detect "openWB Buchse"
	# 	if [ ! -f /home/pi/ppbuchse ]; then
	# 		echo "32" > /home/pi/ppbuchse
	# 	fi
	# 	if ps ax |grep -v grep |grep "python3 ${OPENWBBASEDIR}/runs/buchse.py" > /dev/null
	# 	then
	# 		sudo kill $(ps aux |grep '[b]uchse.py' | awk '{print $2}')
	# 	fi
	# 	python3 ${OPENWBBASEDIR}/runs/buchse.py &
	# fi

	# update display configuration
	# echo "display update..."
	# if grep -Fq "@chromium-browser --incognito --disable-pinch --kiosk http://localhost/openWB/web/display/" /home/pi/.config/lxsession/LXDE-pi/autostart
	# then
	# 	sed -i "s,@chromium-browser --incognito --disable-pinch --kiosk http://localhost/openWB/web/display/,@chromium-browser --incognito --disable-pinch --overscroll-history-navigation=0 --kiosk http://localhost/openWB/web/display/,g" /home/pi/.config/lxsession/LXDE-pi/autostart
	# fi

	# get local ip
	mosquitto_pub -t "openWB/system/ip_address" -p 1886 -r -m "\"$(ip route get 1 | awk '{print $7;exit}')\""

	# update current published versions
	echo "load versions..."
	"$OPENWBBASEDIR/runs/update_available_versions.sh"
	# # and record the current commit details
	# commitId=$(git -C "${OPENWBBASEDIR}/" log --format="%h" -n 1)
	# echo "$commitId" > "${OPENWBBASEDIR}/ramdisk/currentCommitHash"
	# git -C "${OPENWBBASEDIR}/" branch -a --contains "$commitId" | perl -nle 'm|.*origin/(.+).*|; print $1' | uniq | xargs > "${OPENWBBASEDIR}/ramdisk/currentCommitBranches"

	# set restore dir permissions to allow file upload for apache
	sudo chgrp www-data "${OPENWBBASEDIR}/data/restore" "${OPENWBBASEDIR}/data/restore/"*
	sudo chmod g+w "${OPENWBBASEDIR}/data/restore" "${OPENWBBASEDIR}/data/restore/"*

	# set upload limit in php
	# echo -n "fix upload limit..."
	# if [ -d "/etc/php/7.3/" ]; then
	# 	echo "OS Buster"
	# 	sudo /bin/su -c "echo 'upload_max_filesize = 300M' > /etc/php/7.3/apache2/conf.d/20-uploadlimit.ini"
	# 	sudo /bin/su -c "echo 'post_max_size = 300M' >> /etc/php/7.3/apache2/conf.d/20-uploadlimit.ini"
	# fi
	# sudo /usr/sbin/apachectl -k graceful

	# all done, remove boot and update status
	echo "$(date +"%Y-%m-%d %H:%M:%S:")" "boot done :-)"
	mosquitto_pub -p 1886 -t "openWB/system/update_in_progress" -r -m 'false'
	mosquitto_pub -p 1886 -t "openWB/system/reloadDisplay" -m "1"
	touch "${OPENWBBASEDIR}/ramdisk/bootdone"
} >>"$LOGFILE" 2>&1
