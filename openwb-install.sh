#!/bin/bash

echo "install required packages..."
apt-get update
apt-get -q -y install vim bc apache2 php php-gd php-curl php-xml php-json libapache2-mod-php jq git mosquitto mosquitto-clients socat python3-pip sshpass
echo "...done"

echo "check for initial git clone"
if [ ! -d /var/www/html/openWB/web ]; then
	cd /var/www/html/
	git clone https://github.com/openWB/core.git -o openWB --branch master
	chown -R pi:pi openWB
	echo "... git cloned"
else
	echo "...ok"
fi

echo "check for ramdisk"
if grep -Fxq "tmpfs /var/www/html/openWB/ramdisk tmpfs nodev,nosuid,size=32M 0 0" /etc/fstab
then
	echo "...ok"
else
	mkdir -p /var/www/html/openWB/ramdisk
	echo "tmpfs /var/www/html/openWB/ramdisk tmpfs nodev,nosuid,size=32M 0 0" >> /etc/fstab
	mount -a
	echo "...created"
fi

echo "check for crontab"
if grep -Fxq "@reboot /var/www/html/openWB/runs/atreboot.sh &" /var/spool/cron/crontabs/root
then
	echo "...ok"
else
	echo "@reboot /var/www/html/openWB/runs/atreboot.sh &" >> /tmp/tocrontab
	crontab -l -u root | cat - /tmp/tocrontab | crontab -u root -
	rm /tmp/tocrontab
	echo "...added"
fi

# start mosquitto
sudo service mosquitto start

# check for mosquitto configuration
if [ ! -f /etc/mosquitto/conf.d/openwb.conf ]; then
	echo "updating mosquitto config file"
	sudo cp /var/www/html/openWB/web/files/mosquitto.conf /etc/mosquitto/conf.d/openwb.conf
	sudo service mosquitto reload
fi

# echo "disable cronjob logging"
# if grep -Fxq "EXTRA_OPTS=\"-L 0\"" /etc/default/cron
# then
# 	echo "...ok"
# else
# 	echo "EXTRA_OPTS=\"-L 0\"" >> /etc/default/cron
# fi

# apache upload limit
echo -n "fix upload limit..."
if [ -d "/etc/php/7.3/" ]; then
	echo "OS Buster"
	sudo /bin/su -c "echo 'upload_max_filesize = 300M' > /etc/php/7.3/apache2/conf.d/20-uploadlimit.ini"
	sudo /bin/su -c "echo 'post_max_size = 300M' >> /etc/php/7.3/apache2/conf.d/20-uploadlimit.ini"
elif [ -d "/etc/php/7.4/" ]; then
	echo "OS Bullseye"
	sudo /bin/su -c "echo 'upload_max_filesize = 300M' > /etc/php/7.4/apache2/conf.d/20-uploadlimit.ini"
	sudo /bin/su -c "echo 'post_max_size = 300M' >> /etc/php/7.4/apache2/conf.d/20-uploadlimit.ini"
fi

echo "installing python requirements..."
sudo pip install -r /var/www/html/openWB/requirements.txt

# echo "www-data ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers.d/010_pi-nopasswd

# chmod 777 /var/www/html/openWB/openwb.conf
# chmod +x /var/www/html/openWB/modules/*
chmod +x /var/www/html/openWB/runs/*
chmod +x /var/www/html/openWB/*.sh
touch /var/log/openWB.log
chmod 777 /var/log/openWB.log
/var/www/html/openWB/runs/atreboot.sh
