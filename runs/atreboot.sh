#!/bin/bash
OPENWBBASEDIR=$(cd `dirname $0`/../ && pwd)
RAMDISKDIR="${OPENWBBASEDIR}/ramdisk"

echo "atreboot.sh started"
rm "${RAMDISKDIR}/ramdisk/bootdone"
mosquitto_pub -p 1886 -t openWB/system/boot_done -r -m 'false'
(sleep 600; sudo kill $(ps aux |grep '[a]treboot.sh' | awk '{print $2}')) &

if [ -f ${RAMDISKDIR}/ramdisk/bootinprogress ]; then
	rm ${RAMDISKDIR}/ramdisk/bootinprogress
fi

# initialize automatic phase switching
# alpha image restricted to standalone installation!
# if (( u1p3paktiv == 1 )); then
# 	echo "triginit..."
# 	# quick init of phase switching with default pause duration (2s)
# 	sudo python ${RAMDISKDIR}/runs/triginit.py
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
	sudo cp ${RAMDISKDIR}/data/config/000-default.conf /etc/apache2/sites-available/
	echo "...changed"
fi

# if ! sudo grep -Fq "atreboot.sh" /var/spool/cron/crontabs/pi
# then
# 	(crontab -l -u pi ; echo "@reboot ${RAMDISKDIR}/runs/atreboot.sh >> /var/log/openWB.log 2>&1")| crontab -u pi -
# fi

# check for needed packages
echo "apt packages..."
# nothing here yet, all in install.sh

# check for mosquitto configuration
if [ ! -f /etc/mosquitto/conf.d/openwb.conf ] || ! sudo grep -Fq "persistent_client_expiration" /etc/mosquitto/mosquitto.conf; then
	echo "updating mosquitto config file"
	sudo cp ${RAMDISKDIR}/data/config/openwb.conf /etc/mosquitto/conf.d/openwb.conf
	sudo service mosquitto reload
fi

#check for mosquitto_local instance
if [ ! -f /etc/mosquitto/mosquitto_local.conf ]; then
	echo "setting up mosquitto local instance"
	sudo install -d -m 0755 -o root -g root /etc/mosquitto/conf_local.d/
	sudo install -d -m 0755 -o mosquitto -g root /var/lib/mosquitto_local
	sudo cp -a ${RAMDISKDIR}/data/config/mosquitto_local.conf /etc/mosquitto/mosquitto_local.conf
	sudo cp -a ${RAMDISKDIR}/data/config/openwb_local.conf /etc/mosquitto/conf_local.d/

	sudo cp ${RAMDISKDIR}/data/config/mosquitto_local_init /etc/init.d/mosquitto_local
	sudo chown root.root /etc/init.d/mosquitto_local
	sudo chmod 755 /etc/init.d/mosquitto_local
else
	sudo cp -a ${RAMDISKDIR}/data/config/openwb_local.conf /etc/mosquitto/conf_local.d/
fi
sudo systemctl daemon-reload
sudo service mosquitto_local start

# check for other dependencies
echo "python packages..."
sudo pip3 install -r ${RAMDISKDIR}/requirements.txt

# update version
echo "version..."
uuid=$(</sys/class/net/eth0/address)
owbv=$(<${RAMDISKDIR}/web/version)
# curl --connect-timeout 10 -d "update="$releasetrain$uuid"vers"$owbv"" -H "Content-Type: application/x-www-form-urlencoded" -X POST https://openwb.de/tools/update.php

# check for slave config and start handler
# alpha image restricted to standalone installation!
# if (( isss == 1 )); then
# 	echo "isss..."
# 	echo $lastmanagement > ${RAMDISKDIR}/ramdisk/issslp2act
# 	if ps ax |grep -v grep |grep "python3 ${RAMDISKDIR}/runs/isss.py" > /dev/null
# 	then
# 		sudo kill $(ps aux |grep '[i]sss.py' | awk '{print $2}')
# 	fi
# 	python3 ${RAMDISKDIR}/runs/isss.py &
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
# 	if ps ax |grep -v grep |grep "python3 ${RAMDISKDIR}/runs/buchse.py" > /dev/null
# 	then
# 		sudo kill $(ps aux |grep '[b]uchse.py' | awk '{print $2}')
# 	fi
# 	python3 ${RAMDISKDIR}/runs/buchse.py &
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
# curl --connect-timeout 10 -s https://raw.githubusercontent.com/snaptec/openWB/master/web/version > ${RAMDISKDIR}/ramdisk/vnightly
# curl --connect-timeout 10 -s https://raw.githubusercontent.com/snaptec/openWB/beta/web/version > ${RAMDISKDIR}/ramdisk/vbeta
# curl --connect-timeout 10 -s https://raw.githubusercontent.com/snaptec/openWB/stable/web/version > ${RAMDISKDIR}/ramdisk/vstable

# update our local version
sudo git -C /var/www/html/openWB show --pretty='format:%ci [%h]' | head -n1 > ${RAMDISKDIR}/web/lastcommit
# and record the current commit details
commitId=`git -C /var/www/html/openWB log --format="%h" -n 1`
echo $commitId > ${RAMDISKDIR}/ramdisk/currentCommitHash
echo `git -C /var/www/html/openWB branch -a --contains $commitId | perl -nle 'm|.*origin/(.+).*|; print $1' | uniq | xargs` > ${RAMDISKDIR}/ramdisk/currentCommitBranches

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
touch ${RAMDISKDIR}/ramdisk/bootdone
