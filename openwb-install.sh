#!/bin/bash
OPENWBBASEDIR=/var/www/html/openWB
OPENWB_USER=openwb
OPENWB_GROUP=openwb
# TODO: Update the branch for installation as needed
CHECKOUT_BRANCH=trixie-next

if (( $(id -u) != 0 )); then
	echo "this script has to be run as user root or with sudo"
	exit 1
fi

echo "installing openWB 2 into \"${OPENWBBASEDIR}\""

# install packages by pre-downloading our script so we only have one file to maintain
curl -s "https://raw.githubusercontent.com/openWB/core/${CHECKOUT_BRANCH}/runs/install_packages.sh" | bash -s

echo "create group $OPENWB_GROUP"
# Will do nothing if group already exists:
/usr/sbin/groupadd "$OPENWB_GROUP"
echo "done"

echo "create user $OPENWB_USER"
# Will do nothing if user already exists:
/usr/sbin/useradd "$OPENWB_USER" -g "$OPENWB_GROUP" --create-home
echo "done"

# The user "openwb" is still new and we might need sudo in many places. Thus for now we give the user
# unrestricted sudo.
# TODO: Restrict sudo privileges for the openwb user in the future instead of giving unrestricted access.
echo "$OPENWB_USER ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/openwb
chmod 440 /etc/sudoers.d/openwb
echo "done"

echo "check for initial git clone..."
if [ ! -d "${OPENWBBASEDIR}/web" ]; then
	mkdir "$OPENWBBASEDIR"
	chown "$OPENWB_USER:$OPENWB_GROUP" "$OPENWBBASEDIR"
	sudo -u "$OPENWB_USER" git clone https://github.com/openWB/core.git --branch "$CHECKOUT_BRANCH" "$OPENWBBASEDIR"
	echo "git cloned"
else
	echo "ok"
fi

echo -n "check for ramdisk... "
RAMDISK_TARGET_DIR=/etc/systemd/zram-generator.cond.d
RAMDISK_FILE=99-openwb-ramdisk.conf
if [ -f "${RAMDISK_TARGET_DIR}/${RAMDISK_FILE}" ]; then
	echo "ok"
else
	mkdir -p "${OPENWBBASEDIR}/ramdisk"
	sudo mkdir -p "${RAMDISK_TARGET_DIR}"
	sudo cp "${OPENWBBASEDIR}/data/config/${RAMDISK_FILE}" "${RAMDISK_TARGET_DIR}/${RAMDISK_FILE}"
	sudo systemctl daemon-reload
	sudo systemctl restart systemd-zram-setup@zram1.service
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
echo "updating mosquitto config file"
systemctl stop mosquitto
sleep 2
SRC="${OPENWBBASEDIR}/data/config/mosquitto/public"
cp -a "${SRC}/mosquitto.conf" "${SRC}/mosquitto.acl" /etc/mosquitto/
sudo chown mosquitto:mosquitto /etc/mosquitto/mosquitto.acl
sudo chmod 700 /etc/mosquitto/mosquitto.acl
# enable default listeners: local bridge, public secure and unsecure mqtt and ws listeners with acl files
cp -a "${SRC}/openwb.conf" "${SRC}/openwb-unsecure-acl.conf" "${SRC}/openwb-default-acl.conf" /etc/mosquitto/conf.d/
sudo cp /etc/ssl/certs/ssl-cert-snakeoil.pem /etc/mosquitto/certs/openwb.pem
sudo cp /etc/ssl/private/ssl-cert-snakeoil.key /etc/mosquitto/certs/openwb.key
sudo chgrp mosquitto /etc/mosquitto/certs/openwb.key
systemctl start mosquitto

#check for mosquitto_local instance
SRC="${OPENWBBASEDIR}/data/config/mosquitto/local"
if [ ! -f /etc/init.d/mosquitto_local ]; then
	echo "setting up mosquitto local instance"
	install -d -m 0755 -o root -g root /etc/mosquitto/conf_local.d/
	install -d -m 0755 -o mosquitto -g root /var/lib/mosquitto_local
	cp "${SRC}/mosquitto_local_init" /etc/init.d/mosquitto_local
	chown root:root /etc/init.d/mosquitto_local
	chmod 755 /etc/init.d/mosquitto_local
	systemctl daemon-reload
	systemctl enable mosquitto_local
else
	systemctl stop mosquitto_local
	sleep 2
fi
cp -a "${SRC}/mosquitto_local.conf" /etc/mosquitto/
cp -a "${SRC}/openwb_local.conf" /etc/mosquitto/conf_local.d/
systemctl start mosquitto_local
echo "mosquitto done"

# apache
echo -n "replacing apache default page..."
cp "${OPENWBBASEDIR}/data/config/apache/000-default.conf" "/etc/apache2/sites-available/"
cp "${OPENWBBASEDIR}/index.html" /var/www/html/index.html
echo "done"
echo -n "fix upload limit..."
for php_dir in /etc/php/*; do
	if [ -d "$php_dir/apache2/conf.d" ]; then
		echo "upload_max_filesize = 300M" > "$php_dir/apache2/conf.d/20-uploadlimit.ini"
		echo "post_max_size = 300M" >> "$php_dir/apache2/conf.d/20-uploadlimit.ini"
		echo "done for: $php_dir"
	fi
done
echo -n "enabling apache ssl module..."
a2enmod ssl
a2enmod proxy_wstunnel
sudo a2dissite default-ssl
sudo cp "${OPENWBBASEDIR}/data/config/apache/apache-openwb-ssl.conf" /etc/apache2/sites-available/ 
sudo a2ensite apache-openwb-ssl
echo "done"
echo -n "restarting apache..."
systemctl restart apache2
echo "done"

echo "installing python requirements..."
python_build_packages=()
python_binary_packages=()
case $(dpkg --print-architecture) in
	arm64) python_binary_packages=(python3-evdev) ;;
	arm*) ;;
	*) python_build_packages=(gcc python3-dev) ;;
esac
if ! apt-get -q -y install python3-venv "${python_build_packages[@]}" "${python_binary_packages[@]}"; then
	echo "Failed to install Python environment prerequisites" >&2
	exit 1
fi
venv_status=0
sudo -u "$OPENWB_USER" bash "${OPENWBBASEDIR}/runs/setup_python_venv.sh" "$OPENWBBASEDIR" 1 || venv_status=$?
if ((venv_status != 0 && venv_status != 10)); then
	echo "Python environment installation failed" >&2
	exit 1
fi

echo "installing openwb2 system service..."
ln -s "${OPENWBBASEDIR}/data/config/openwb2.service" /etc/systemd/system/openwb2.service
systemctl daemon-reload
systemctl enable openwb2

echo "installing openwb2-simpleAPI service..."
ln -s "${OPENWBBASEDIR}/data/config/openwb-simpleAPI.service" /etc/systemd/system/openwb-simpleAPI.service
systemctl daemon-reload
systemctl enable openwb-simpleAPI

echo "installing openwb2 remote support service..."
cp "${OPENWBBASEDIR}/data/config/openwbRemoteSupport.service" /etc/systemd/system/openwbRemoteSupport.service
systemctl daemon-reload
systemctl enable openwbRemoteSupport
systemctl start openwbRemoteSupport

echo "installation finished, now starting openwb services..."
systemctl start openwb2
systemctl start openwb-simpleAPI

echo "all done"
echo "if you want to use this installation for development, add a password for user 'openwb'"
