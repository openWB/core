#!/bin/bash
OPENWBBASEDIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

if (( $(id -u) != 0 )); then
	echo "this script has to be run as root or with sudo"
	exit 1
fi

case "$1" in
	"clearall")
		echo "deleting retained message store of external mosquitto..."
		timeout 3 mosquitto_sub -t '#' --remove-retained --retained-only
		echo "deleting retained message store of internal mosquitto..."
		timeout 3 mosquitto_sub -t '#' --remove-retained --retained-only -p 1886
		echo "deleting log data"
		rm -r "$OPENWBBASEDIR/data/charge_log/"* "$OPENWBBASEDIR/data/daily_log/"* "$OPENWBBASEDIR/data/log/"*.log "$OPENWBBASEDIR/data/monthly_log/"*
		echo "all done";;
	*)
		echo "please pass \"clearall\" as parameter if you really want to reset all data stored in the internal and external broker"
		exit 1;;
esac
