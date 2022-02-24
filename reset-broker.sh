#!/bin/bash
case "$1" in
	"clearall")
		sudo systemctl stop openwb2.service
		echo "deleting retained message store of external mosquitto..."
		timeout 3 mosquitto_sub -t '#' --remove-retained --retained-only
		echo "deleting retained message store of internal mosquitto..."
		timeout 3 mosquitto_sub -t '#' --remove-retained --retained-only -p 1886
		sudo systemctl start openwb2.service
		echo "reset done, now running atreboot.sh..."
		./runs/atreboot.sh
		echo "all done";;
	*)
		echo "please pass \"clearall\" as parameter if you really want to reset all data stored in the internal and external broker"
		exit 1;;
esac
