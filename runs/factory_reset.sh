#!/bin/bash
OPENWBBASEDIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

if (( $(id -u) != 0 )); then
	echo "this script has to be run as root or with sudo"
	exit 1
fi

case "$1" in
	"clearall")
		echo "checking for configured cloud bridge..."
		cloud_bridge=$(timeout 1 mosquitto_sub -t 'openWB/system/mqtt/bridge/+' | grep -E '"is_openwb_cloud": ?true')
		if [ -n "$cloud_bridge" ]; then
			echo "cloud bridge is configured"
			valid_partner_ids=$(timeout 1 mosquitto_sub -t 'openWB/system/mqtt/valid_partner_ids' -C 1)
		else
			echo "no cloud bridge configured"
		fi
		echo "deleting retained message store of external mosquitto..."
		timeout 3 mosquitto_sub -t '#' --remove-retained --retained-only
		echo "deleting retained message store of internal mosquitto..."
		timeout 3 mosquitto_sub -t '#' --remove-retained --retained-only -p 1886
		echo "deleting log data"
		rm -r "$OPENWBBASEDIR/data/charge_log/"* "$OPENWBBASEDIR/data/daily_log/"* "$OPENWBBASEDIR/data/log/"*.log "$OPENWBBASEDIR/data/monthly_log/"*
		echo "reset display rotation"
		sudo sed -i "s/^lcd_rotate=[0-3]$/lcd_rotate=0/" "/boot/config.txt"
		if [ -n "$cloud_bridge" ]; then
			echo "restore cloud bridge configuration: $cloud_bridge"
			mosquitto_pub -t 'openWB/command/max_id/mqtt_bridge' -r -m 1 -p 1886
			mosquitto_pub -t 'openWB/system/mqtt/valid_partner_ids' -r -m "$valid_partner_ids" -p 1886
			mosquitto_pub -t 'openWB/system/mqtt/bridge/0' -r -m "$cloud_bridge" -p 1886
		fi
		echo "all done";;
	*)
		echo "please pass \"clearall\" as parameter if you really want to reset all data stored in the internal and external broker"
		exit 1;;
esac
