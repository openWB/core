#!/bin/bash
OPENWBBASEDIR=/var/www/html/openWB

echo "installing openWB 2 into \"${OPENWBBASEDIR}\""

echo "install required packages..."
apt-get update
apt-get -q -y install vim bc jq git mosquitto mosquitto-clients socat python3-pip sshpass
echo "done"

echo "check for initial git clone..."
if [ ! -d ${OPENWBBASEDIR}/web ]; then
	cd /var/www/html/
	git clone https://github.com/openWB/core.git --branch master ${OPENWBBASEDIR}
	chown -R pi:pi openWB
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
	sudo cp ${OPENWBBASEDIR}/data/config/openwb.cron /etc/cron.d/openwb
	echo "installed"
else
	echo "ok"
fi

# check for mosquitto configuration
echo "check mosquitto installation..."
if [ ! -f /etc/mosquitto/conf.d/openwb.conf ] || ! sudo grep -Fq "persistent_client_expiration" /etc/mosquitto/mosquitto.conf; then
	echo "updating mosquitto config file"
	sudo cp ${OPENWBBASEDIR}/data/config/openwb.conf /etc/mosquitto/conf.d/openwb.conf
	sudo service mosquitto restart
fi

#check for mosquitto_local instance
if [ ! -f /etc/mosquitto/mosquitto_local.conf ]; then
	echo "setting up mosquitto local instance"
	sudo install -d -m 0755 -o root -g root /etc/mosquitto/conf_local.d/
	sudo install -d -m 0755 -o mosquitto -g root /var/lib/mosquitto_local
	sudo cp -a ${OPENWBBASEDIR}/data/config/mosquitto_local.conf /etc/mosquitto/mosquitto_local.conf
	sudo cp -a ${OPENWBBASEDIR}/data/config/openwb_local.conf /etc/mosquitto/conf_local.d/

	sudo cp ${OPENWBBASEDIR}/data/config/mosquitto_local_init /etc/init.d/mosquitto_local
	sudo chown root.root /etc/init.d/mosquitto_local
	sudo chmod 755 /etc/init.d/mosquitto_local
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

echo "installing python requirements..."
sudo pip install -r ${OPENWBBASEDIR}/requirements.txt

# echo "www-data ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers.d/010_pi-nopasswd

# chmod 777 ${OPENWBBASEDIR}/openwb.conf
# chmod +x ${OPENWBBASEDIR}/modules/*
chmod +x ${OPENWBBASEDIR}/runs/*
chmod +x ${OPENWBBASEDIR}/*.sh
touch /var/log/openWB.log
chmod 777 /var/log/openWB.log

echo "installing openwb2 system service..."
sudo ln -s ${OPENWBBASEDIR}/data/config/openwb2.service /etc/systemd/system/openwb2.service
sudo systemctl daemon-reload
sudo systemctl enable openwb2.service
sudo systemctl start openwb2.service

echo "installation finished, now running atreboot.sh..."
${OPENWBBASEDIR}/runs/atreboot.sh
