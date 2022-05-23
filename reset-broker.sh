#!/bin/bash
OPENWBBASEDIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

if (( $(id -u) != 0 )); then
	echo "this script has to be run with sudo"
	exit 1
fi

case "$1" in
	"clearall")
		echo "stopping openwb2 service..."
		systemctl stop openwb2.service
		echo "deleting retained message store of external mosquitto..."
		timeout 3 mosquitto_sub -t '#' --remove-retained --retained-only
		echo "deleting retained message store of internal mosquitto..."
		timeout 3 mosquitto_sub -t '#' --remove-retained --retained-only -p 1886
		echo "starting openwb2 service..."
		systemctl start openwb2.service
		echo "reset done, now running atreboot.sh..."
		"${OPENWBBASEDIR}/runs/atreboot.sh"
		echo "all done";;
	*)
		echo "please pass \"clearall\" as parameter if you really want to reset all data stored in the internal and external broker"
		exit 1;;
esac
