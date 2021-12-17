#!/bin/bash
echo "atreboot.sh started"
rm "/var/www/html/openWB/ramdisk/bootdone"
mosquitto_pub -p 1886 -t openWB/system/boot_done -r -m 'false'
(sleep 600; sudo kill $(ps aux |grep '[a]treboot.sh' | awk '{print $2}')) &

if [ -f /var/www/html/openWB/ramdisk/bootinprogress ]; then
	rm /var/www/html/openWB/ramdisk/bootinprogress
fi

# standard socket - activated after reboot due to RASPI init defaults so we need to disable it as soon as we can
if [[ $standardSocketInstalled == "1" ]]; then
	echo "turning off standard socket ..."
	sudo python /var/www/html/openWB/runs/standardSocket.py off
fi

# initialize automatic phase switching
if (( u1p3paktiv == 1 )); then
	echo "triginit..."
	# quick init of phase switching with default pause duration (2s)
	sudo python /var/www/html/openWB/runs/triginit.py
fi

# check if tesla wall connector is configured and start daemon
if [[ $evsecon == twcmanager ]]; then
	echo "twcmanager..."
	if [[ $twcmanagerlp1ip == "localhost/TWC" ]]; then
		screen -dm -S TWCManager /var/www/html/TWC/TWCManager.py &
	fi
fi

# check if display is configured and setup timeout
if (( displayaktiv == 1 )); then
	echo "display..."
	if ! grep -Fq "pinch" /home/pi/.config/lxsession/LXDE-pi/autostart
	then
		echo "not found"
		echo "@xscreensaver -no-splash" > /home/pi/.config/lxsession/LXDE-pi/autostart
		echo "@point-rpi" >> /home/pi/.config/lxsession/LXDE-pi/autostart
		echo "@xset s 600" >> /home/pi/.config/lxsession/LXDE-pi/autostart
		echo "@chromium-browser --incognito --disable-pinch --kiosk http://localhost/openWB/web/display.php" >> /home/pi/.config/lxsession/LXDE-pi/autostart
	fi
	echo "deleting browser cache"
	rm -rf /home/pi/.cache/chromium
fi

# check for LAN/WLAN connection
echo "LAN/WLAN..."
ethstate=$(</sys/class/net/eth0/carrier)
if (( ethstate == 1 )); then
	sudo ifconfig eth0:0 $virtual_ip_eth0 netmask 255.255.255.0 up
else
	sudo ifconfig wlan0:0 $virtual_ip_wlan0 netmask 255.255.255.0 up
fi

# check for apache configuration
echo "apache..."
if grep -Fxq "AllowOverride" /etc/apache2/sites-available/000-default.conf
then
	echo "...ok"
else
	sudo cp /var/www/html/openWB/web/tools/000-default.conf /etc/apache2/sites-available/
	echo "...changed"
fi

if ! sudo grep -Fq "atreboot.sh" /var/spool/cron/crontabs/pi
then
	(crontab -l -u pi ; echo "@reboot /var/www/html/openWB/runs/atreboot.sh >> /var/log/openWB.log 2>&1")| crontab -u pi -
fi

# check for needed packages
echo "packages 1..."
if python -c "import evdev" &> /dev/null; then
	echo 'evdev installed...'
else
	sudo pip install evdev
fi
if ! [ -x "$(command -v sshpass)" ];then
	sudo apt-get -qq update
	sleep 1
	sudo apt-get -qq install sshpass
fi
if [ $(dpkg-query -W -f='${Status}' php-gd 2>/dev/null | grep -c "ok installed") -eq 0 ];
then
	sudo apt-get -qq update
	sleep 1
	sudo apt-get -qq install -y php-gd
	sleep 1
	sudo apt-get -qq install -y php7.0-xml
fi

# setup timezone
echo "timezone..."
sudo cp /usr/share/zoneinfo/Europe/Berlin /etc/localtime


if [ ! -f /home/pi/ssl_patched ]; then 
	sudo apt-get update 
	sudo apt-get -qq install -y openssl libcurl3 curl libgcrypt20 libgnutls30 libssl1.1 libcurl3-gnutls libssl1.0.2 php7.0-cli php7.0-gd php7.0-opcache php7.0 php7.0-common php7.0-json php7.0-readline php7.0-xml php7.0-curl libapache2-mod-php7.0 
	touch /home/pi/ssl_patched 
fi


# check for mosquitto packages
echo "mosquitto..."
if [ ! -f /etc/mosquitto/mosquitto.conf ]; then
	sudo apt-get update
	sudo apt-get -qq install -y mosquitto mosquitto-clients
	sudo service mosquitto start
fi

# check for mosquitto configuration
if [ ! -f /etc/mosquitto/conf.d/openwb.conf ] || ! sudo grep -Fq "persistent_client_expiration" /etc/mosquitto/mosquitto.conf; then
	echo "updating mosquitto config file"
	sudo cp /var/www/html/openWB/data/config/openwb.conf /etc/mosquitto/conf.d/openwb.conf
	sudo service mosquitto reload
fi

#check for mosquitto_local instance
if [ ! -f /etc/mosquitto/mosquitto_local.conf ]; then
	echo "setting up mosquitto local instance"
	sudo install -d -m 0755 -o root -g root /etc/mosquitto/conf_local.d/
	sudo install -d -m 0755 -o mosquitto -g root /var/lib/mosquitto_local
	sudo cp -a /var/www/html/openWB/data/config/mosquitto_local.conf /etc/mosquitto/mosquitto_local.conf
	sudo cp -a /var/www/html/openWB/data/config/openwb_local.conf /etc/mosquitto/conf_local.d/

	sudo cp /var/www/html/openWB/data/config/mosquitto_local_init /etc/init.d/mosquitto_local
	sudo chown root.root /etc/init.d/mosquitto_local
	sudo chmod 755 /etc/init.d/mosquitto_local
else
	sudo cp -a /var/www/html/openWB/data/config/openwb_local.conf /etc/mosquitto/conf_local.d/
fi
sudo systemctl daemon-reload
sudo service mosquitto_local start

# check for other dependencies
echo "packages 2..."
if python3 -c "import paho.mqtt.publish as publish" &> /dev/null; then
	echo 'mqtt installed...'
else
	sudo apt-get -qq install -y python3-pip
	sudo pip3 install paho-mqtt
fi
if python3 -c "import docopt" &> /dev/null; then
	echo 'docopt installed...'
else
	sudo pip3 install docopt
fi
if python3 -c "import certifi" &> /dev/null; then
	echo 'certifi installed...'
else
	sudo pip3 install certifi
fi
if python3 -c "import aiohttp" &> /dev/null; then
	echo 'aiohttp installed...'
else
	sudo pip3 install aiohttp
fi
if python3 -c "import pymodbus" &> /dev/null; then
	echo 'pymodbus installed...'
else
	sudo pip3 install pymodbus
fi
if python3 -c "import requests" &> /dev/null; then
	echo 'python requests installed...'
else
	sudo pip3 install requests
fi
#Prepare for jq in Python
if python3 -c "import jq" &> /dev/null; then
	echo 'jq installed...'
else
	sudo pip3 install jq
fi
#Prepare for ipparser in Python
if python3 -c "import ipparser" &> /dev/null; then
	echo 'ipparser installed...'
else
	sudo pip3 install ipparser
fi

# update version
echo "version..."
uuid=$(</sys/class/net/eth0/address)
owbv=$(</var/www/html/openWB/web/version)
curl -d "update="$releasetrain$uuid"vers"$owbv"" -H "Content-Type: application/x-www-form-urlencoded" -X POST https://openwb.de/tools/update.php

# check for slave config and start handler
if (( isss == 1 )); then
	echo "isss..."
	echo $lastmanagement > /var/www/html/openWB/ramdisk/issslp2act
	if ps ax |grep -v grep |grep "python3 /var/www/html/openWB/runs/isss.py" > /dev/null
	then
		sudo kill $(ps aux |grep '[i]sss.py' | awk '{print $2}')
	fi
	python3 /var/www/html/openWB/runs/isss.py &
	# second IP already set up !
	ethstate=$(</sys/class/net/eth0/carrier)
	if (( ethstate == 1 )); then
		sudo ifconfig eth0:0 $virtual_ip_eth0 netmask 255.255.255.0 down
	else
		sudo ifconfig wlan0:0 $virtual_ip_wlan0 netmask 255.255.255.0 down
	fi
fi

# check for socket system and start handler
if [[ "$evsecon" == "buchse" ]]  && [[ "$isss" == "0" ]]; then
	echo "socket..."
	# ppbuchse is used in issss.py to detect "openWB Buchse"
	if [ ! -f /home/pi/ppbuchse ]; then
		echo "32" > /home/pi/ppbuchse
	fi
	if ps ax |grep -v grep |grep "python3 /var/www/html/openWB/runs/buchse.py" > /dev/null
	then
		sudo kill $(ps aux |grep '[b]uchse.py' | awk '{print $2}')
	fi
	python3 /var/www/html/openWB/runs/buchse.py &
fi

# update display configuration
echo "display update..."
if grep -Fq "@chromium-browser --incognito --disable-pinch --kiosk http://localhost/openWB/web/display.php" /home/pi/.config/lxsession/LXDE-pi/autostart
then
	sed -i "s,@chromium-browser --incognito --disable-pinch --kiosk http://localhost/openWB/web/display.php,@chromium-browser --incognito --disable-pinch --overscroll-history-navigation=0 --kiosk http://localhost/openWB/web/display.php,g" /home/pi/.config/lxsession/LXDE-pi/autostart
fi

# get local ip
mosquitto_pub -t openWB/system/ip_address -p 1886 -r -m "\"$(ip route get 1 | awk '{print $7;exit}')\""
# update current published versions
echo "load versions..."
curl -s https://raw.githubusercontent.com/snaptec/openWB/master/web/version > /var/www/html/openWB/ramdisk/vnightly
curl -s https://raw.githubusercontent.com/snaptec/openWB/beta/web/version > /var/www/html/openWB/ramdisk/vbeta
curl -s https://raw.githubusercontent.com/snaptec/openWB/stable/web/version > /var/www/html/openWB/ramdisk/vstable

# update our local version
sudo git -C /var/www/html/openWB show --pretty='format:%ci [%h]' | head -n1 > /var/www/html/openWB/web/lastcommit

# set upload limit in php
#prepare for Buster
echo -n "fix upload limit..."
if [ -d "/etc/php/7.0/" ]; then
	echo "OS Stretch"
	sudo /bin/su -c "echo 'upload_max_filesize = 300M' > /etc/php/7.0/apache2/conf.d/20-uploadlimit.ini"
	sudo /bin/su -c "echo 'post_max_size = 300M' >> /etc/php/7.0/apache2/conf.d/20-uploadlimit.ini"
elif [ -d "/etc/php/7.3/" ]; then
	echo "OS Buster"
	sudo /bin/su -c "echo 'upload_max_filesize = 300M' > /etc/php/7.3/apache2/conf.d/20-uploadlimit.ini"
	sudo /bin/su -c "echo 'post_max_size = 300M' >> /etc/php/7.3/apache2/conf.d/20-uploadlimit.ini"
fi
sudo /usr/sbin/apachectl -k graceful

# all done, remove boot and update status
echo $(date +"%Y-%m-%d %H:%M:%S:") "boot done :-)"
mosquitto_pub -p 1886 -t openWB/system/update_in_progress -r -m 'false'
mosquitto_pub -p 1886 -t openWB/system/boot_done -r -m 'true'
mosquitto_pub -t openWB/system/reloadDisplay -m "1"
touch /var/www/html/openWB/ramdisk/bootdone