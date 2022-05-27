#!/bin/bash
OPENWBBASEDIR=/var/www/html/openWB
OPENWB_USER=openwb

if (( $(id -u) != 0 )); then
	echo "this script has to be run as user root or with sudo"
	exit 1
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
# unrestricted sudo. This should be restricted in the future
echo "$OPENWB_USER ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/openwb
echo "done"

echo "check for initial git clone..."
if [ ! -d "${OPENWBBASEDIR}/web" ]; then
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
	mkdir -p "${OPENWBBASEDIR}/ramdisk"
	echo "tmpfs ${OPENWBBASEDIR}/ramdisk tmpfs nodev,nosuid,size=32M 0 0" >> /etc/fstab
	mount -a
	echo "created"
fi

echo -n "check for crontab... "
if [ ! -f /etc/cron.d/openwb ]; then
	cp "${OPENWBBASEDIR}/data/config/openwb.cron" /etc/cron.d/openwb
	echo "installed"
else
	echo "ok"
fi

# check for mosquitto configuration
echo "check mosquitto installation..."
if [ ! -f /etc/mosquitto/conf.d/openwb.conf ] || ! grep -Fq "persistent_client_expiration" /etc/mosquitto/mosquitto.conf; then
	echo "updating mosquitto config file"
	service mosquitto stop
	sleep 2
	cp "${OPENWBBASEDIR}/data/config/openwb.conf" /etc/mosquitto/conf.d/openwb.conf
	service mosquitto start
fi

#check for mosquitto_local instance
if [ ! -f /etc/mosquitto/mosquitto_local.conf ]; then
	echo "setting up mosquitto local instance"
	install -d -m 0755 -o root -g root /etc/mosquitto/conf_local.d/
	install -d -m 0755 -o mosquitto -g root /var/lib/mosquitto_local
	cp -a "${OPENWBBASEDIR}/data/config/mosquitto_local.conf" /etc/mosquitto/mosquitto_local.conf
	cp -a "${OPENWBBASEDIR}/data/config/openwb_local.conf" /etc/mosquitto/conf_local.d/
	cp "${OPENWBBASEDIR}/data/config/mosquitto_local_init" /etc/init.d/mosquitto_local
	chown root:root /etc/init.d/mosquitto_local
	chmod 755 /etc/init.d/mosquitto_local
	systemctl daemon-reload
	systemctl enable mosquitto_local
	service mosquitto_local start
else
	service mosquitto_local stop
	sleep 2
	cp -a "${OPENWBBASEDIR}/data/config/openwb_local.conf" /etc/mosquitto/conf_local.d/
	service mosquitto_local start
fi
echo "mosquitto done"

# apache
echo -n "replacing apache default page..."
cp "${OPENWBBASEDIR}/index.html" /var/www/html/index.html
echo "done"
echo -n "fix upload limit..."
if [ -d "/etc/php/7.3/" ]; then
	echo "upload_max_filesize = 300M" > /etc/php/7.3/apache2/conf.d/20-uploadlimit.ini
	echo "post_max_size = 300M" >> /etc/php/7.3/apache2/conf.d/20-uploadlimit.ini
	echo "done (OS Buster)"
elif [ -d "/etc/php/7.4/" ]; then
	echo "upload_max_filesize = 300M" > /etc/php/7.4/apache2/conf.d/20-uploadlimit.ini
	echo "post_max_size = 300M" >> /etc/php/7.4/apache2/conf.d/20-uploadlimit.ini
	echo "done (OS Bullseye)"
fi

echo "installing python requirements..."
sudo -u "$OPENWB_USER" pip install -r "${OPENWBBASEDIR}/requirements.txt"

echo "installing openwb2 system service..."
ln -s "${OPENWBBASEDIR}/data/config/openwb2.service" /etc/systemd/system/openwb2.service
systemctl daemon-reload
systemctl enable openwb2.service
systemctl start openwb2.service

echo "installation finished, now running atreboot.sh..."
"${OPENWBBASEDIR}/runs/atreboot.sh"
