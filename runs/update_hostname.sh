#!/bin/bash
if (( $# != 1 )); then
	echo "ERROR: no new hostname provided!"
	exit 1
fi

newHostname=$1
echo "changing hostname to $newHostname..."
touch /tmp/tmphostname
echo "$newHostname" > /tmp/tmphostname
sudo mv /tmp/tmphostname /etc/hostname
sudo sed -i "s/127.0.1.1.*/127.0.1.1    $newHostname/" /etc/hosts
# generate new default cert
echo "generating new cert..."
sudo make-ssl-cert generate-default-snakeoil --force-overwrite
# copy certs for mosquitto
sudo cp /etc/ssl/certs/ssl-cert-snakeoil.pem /etc/mosquitto/certs/openwb.pem
sudo cp /etc/ssl/private/ssl-cert-snakeoil.key /etc/mosquitto/certs/openwb.key
sudo chgrp mosquitto /etc/mosquitto/certs/openwb.key
echo "done"
# reboot
echo "rebooting system"
# sudo reboot
