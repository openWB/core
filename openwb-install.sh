#!/bin/bash
OPENWBBASEDIR=/var/www/html/openWB
OPENWB_USER=openwb

if [ "$EUID" -ne 0 ]
then
	echo "This script must be run as root"
	exit
fi

echo "installing openWB 2 into \"${OPENWBBASEDIR}\""

echo "install required packages..."
apt-get update
apt-get -q -y install vim bc apache2 php php-gd php-curl php-xml php-json libapache2-mod-php jq git mosquitto mosquitto-clients socat python3-pip sshpass
echo "done"

echo "create user $OPENWB_USER"
# Will do nothing if user already exists:
useradd "$OPENWB_USER" --create-home
# The user "openwb" is still new and we might need sudo in many places. Thus for now we give the user
# unrestricted sudo. This should restricted in the future
echo "$OPENWB_USER ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/openwb
echo "done"

echo "check for initial git clone..."
if [ ! -d "$OPENWBBASEDIR/web" ]; then
	mkdir "$OPENWBBASEDIR"
	chown "$OPENWB_USER:$OPENWB_USER" "$OPENWBBASEDIR"
	sudo -u "$OPENWB_USER" git clone https://github.com/openWB/core.git --branch master "$OPENWBBASEDIR"
	echo "git cloned"
else
	echo "ok"
fi

echo -n "check for ramdisk... "
if grep -Fxq "tmpfs ${OPENWBBASEDIR}/ramdisk tmpfs nodev,nosuid,size=32M 0 0" /etc/fstab; then
	echo "ok"
else
	mkdir -p ${OPENWBBASEDIR}/ramdisk
	echo "tmpfs ${OPENWBBASEDIR}/ramdisk tmpfs nodev,nosuid,size=32M 0 0" >> /etc/fstab
	mount -a
	echo "created"
fi

echo -n "check for crontab... "
if [ ! -f /etc/cron.d/openwb ]; then
	cp ${OPENWBBASEDIR}/data/config/openwb.cron /etc/cron.d/openwb
	echo "installed"
else
	echo "ok"
fi

# check for mosquitto configuration
echo "check mosquitto installation..."
if [ ! -f /etc/mosquitto/conf.d/openwb.conf ] || ! sudo grep -Fq "persistent_client_expiration" /etc/mosquitto/mosquitto.conf; then
	echo "updating mosquitto config file"
	cp ${OPENWBBASEDIR}/data/config/openwb.conf /etc/mosquitto/conf.d/openwb.conf
	service mosquitto restart
fi

#check for mosquitto_local instance
if [ ! -f /etc/mosquitto/mosquitto_local.conf ]; then
	echo "setting up mosquitto local instance"
	install -d -m 0755 -o root -g root /etc/mosquitto/conf_local.d/
	install -d -m 0755 -o mosquitto -g root /var/lib/mosquitto_local
	cp -a "$OPENWBBASEDIR/data/config/mosquitto_local.conf" /etc/mosquitto/mosquitto_local.conf
	cp -a "$OPENWBBASEDIR/data/config/openwb_local.conf" /etc/mosquitto/conf_local.d/

	cp "$OPENWBBASEDIR/data/config/mosquitto_local_init" /etc/init.d/mosquitto_local
	chown root:root /etc/init.d/mosquitto_local
	chmod 755 /etc/init.d/mosquitto_local
else
	sudo cp -a ${OPENWBBASEDIR}/data/config/openwb_local.conf /etc/mosquitto/conf_local.d/
fi
sudo systemctl daemon-reload
sudo systemctl enable mosquitto_local
sudo service mosquitto_local restart
echo "mosquitto done"

# echo "disable cronjob logging"
# if grep -Fxq "EXTRA_OPTS=\"-L 0\"" /etc/default/cron
# then
# 	echo "...ok"
# else
# 	echo "EXTRA_OPTS=\"-L 0\"" >> /etc/default/cron
# fi

# apache
echo -n "replacing apache default page..."
sudo cp ${OPENWBBASEDIR}/index.html /var/www/html/index.html
echo "done"
echo -n "fix upload limit..."
echo "upload_max_filesize = 300M
post_max_size = 300M" > $(echo /etc/php/*/apache2/conf.d)/20-uploadlimit.ini
echo "done"

echo "installing python requirements..."
sudo -u "$OPENWB_USER" pip install -r "$OPENWBBASEDIR/requirements.txt"

# echo "www-data ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers.d/010_pi-nopasswd

# chmod 777 ${OPENWBBASEDIR}/openwb.conf
# chmod +x ${OPENWBBASEDIR}/modules/*
chmod +x "$OPENWBBASEDIR"/runs/* "$OPENWBBASEDIR"/*.sh
touch /var/log/openWB.log
chown "$OPENWB_USER:$OPENWB_USER" /var/log/openWB.log

echo "installing openwb2 system service..."
ln -s ${OPENWBBASEDIR}/data/config/openwb2.service /etc/systemd/system/openwb2.service
systemctl daemon-reload
systemctl enable openwb2.service
systemctl start openwb2.service

echo "installation finished, now running atreboot.sh..."
${OPENWBBASEDIR}/runs/atreboot.sh
