#!/bin/bash
case "$1" in
	"clearall")
		echo "deleting retained message store of external mosquitto..."
		sudo service mosquitto stop
		sudo rm /var/lib/mosquitto/mosquitto.db
		sudo service mosquitto start
		echo "deleting retained message store of internal mosquitto..."
		sudo service mosquitto_local stop
		sudo rm /var/lib/mosquitto_local/mosquitto.db
		sudo service mosquitto_local start
		sudo rm /etc/mosquitto/mosquitto_local.conf
		echo "reset done, now running atreboot.sh..."
		./runs/atreboot.sh
		echo "all done";;
	*)
		echo "please pass \"clearall\" as parameter if you really want to reset all data stored in the internal and external broker"
		exit 1;;
esac
