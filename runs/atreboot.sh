#!/bin/bash

if [ $(id -u -n) != "openwb" ]
then
	echo "Re-running script ${BASH_SOURCE[0]} as user openwb"
	exec sudo -u openwb bash "${BASH_SOURCE[0]}"
fi

OPENWBBASEDIR=$(cd `dirname $0`/../ && pwd)
echo "atreboot.sh started"
rm "${OPENWBBASEDIR}/ramdisk/bootdone"
mosquitto_pub -p 1886 -t openWB/system/boot_done -r -m 'false'
(sleep 600; sudo kill $(ps aux |grep '[a]treboot.sh' | awk '{print $2}')) &

if [ -f ${OPENWBBASEDIR}/ramdisk/bootinprogress ]; then
	rm ${OPENWBBASEDIR}/ramdisk/bootinprogress
fi

# initialize automatic phase switching
# alpha image restricted to standalone installation!
# if (( u1p3paktiv == 1 )); then
# 	echo "triginit..."
# 	# quick init of phase switching with default pause duration (2s)
# 	sudo python ${OPENWBBASEDIR}/runs/triginit.py
# fi

# check if tesla wall connector is configured and start daemon
# if [[ $evsecon == twcmanager ]]; then
# 	echo "twcmanager..."
# 	if [[ $twcmanagerlp1ip == "localhost/TWC" ]]; then
# 		screen -dm -S TWCManager /var/www/html/TWC/TWCManager.py &
# 	fi
# fi

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
sudo ifconfig eth0:0 192.168.193.5 netmask 255.255.255.0 up

# check for apache configuration
echo "apache..."
if grep -Fxq "AllowOverride" /etc/apache2/sites-available/000-default.conf
then
	echo "...ok"
else
	sudo cp ${OPENWBBASEDIR}/data/config/000-default.conf /etc/apache2/sites-available/
	echo "...changed"
fi

# check for needed packages
echo "apt packages..."
# nothing here yet, all in install.sh

# check for mosquitto configuration
# nothing todo here yet, mosquitto is configured in install-skript

# check for other dependencies
echo "python packages..."
pip3 install -r "$OPENWBBASEDIR/requirements.txt"

# update version
echo "version..."
uuid=$(</sys/class/net/eth0/address)
owbv=$(<${OPENWBBASEDIR}/web/version)
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
mosquitto_pub -t openWB/system/ip_address -p 1886 -r -m "\"$(ip route get 1 | awk '{print $7;exit}')\""
# update current published versions
echo "load versions..."
# change needed after repo is public!
# curl --connect-timeout 10 -s https://raw.githubusercontent.com/snaptec/openWB/master/web/version > ${OPENWBBASEDIR}/ramdisk/vnightly
# curl --connect-timeout 10 -s https://raw.githubusercontent.com/snaptec/openWB/beta/web/version > ${OPENWBBASEDIR}/ramdisk/vbeta
# curl --connect-timeout 10 -s https://raw.githubusercontent.com/snaptec/openWB/stable/web/version > ${OPENWBBASEDIR}/ramdisk/vstable

# update our local version
git -C "$OPENWBBASEDIR/" show --pretty='format:%ci [%h]' | head -n1 > "$OPENWBBASEDIR/web/lastcommit"
# and record the current commit details
commitId=`git -C ${OPENWBBASEDIR}/ log --format="%h" -n 1`
echo "$commitId" > ${OPENWBBASEDIR}/ramdisk/currentCommitHash
git -C "$OPENWBBASEDIR/" branch -a --contains "$commitId" | perl -nle 'm|.*origin/(.+).*|; print $1' | uniq | xargs > "$OPENWBBASEDIR/ramdisk/currentCommitBranches"

# set upload limit in php
# echo -n "fix upload limit..."
# if [ -d "/etc/php/7.3/" ]; then
# 	echo "OS Buster"
# 	sudo /bin/su -c "echo 'upload_max_filesize = 300M' > /etc/php/7.3/apache2/conf.d/20-uploadlimit.ini"
# 	sudo /bin/su -c "echo 'post_max_size = 300M' >> /etc/php/7.3/apache2/conf.d/20-uploadlimit.ini"
# fi
# sudo /usr/sbin/apachectl -k graceful

# all done, remove boot and update status
echo $(date +"%Y-%m-%d %H:%M:%S:") "boot done :-)"
mosquitto_pub -p 1886 -t openWB/system/update_in_progress -r -m 'false'
mosquitto_pub -p 1883 -t openWB/system/update_in_progress -r -m 'false'
mosquitto_pub -p 1886 -t openWB/system/boot_done -r -m 'true'
mosquitto_pub -p 1883 -t openWB/system/boot_done -r -m 'true'
mosquitto_pub -t openWB/system/reloadDisplay -m "1"
touch ${OPENWBBASEDIR}/ramdisk/bootdone
