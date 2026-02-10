#!/bin/bash
{
	echo "Resetting user management..."
	FILE="/var/lib/mosquitto/dynamic-security.json"
	if [ -f $FILE ]; then
		sudo rm /var/lib/mosquitto/dynamic-security.json
		echo "Dynamic security file removed."
	else
		echo "No dynamic security file found."
	fi
	# remove mosquitto_ctrl file if it exists
	if [ -f "/home/openwb/.config/mosquitto_ctrl" ]; then
		echo deleting user management data
		rm /home/openwb/.config/mosquitto_ctrl
	fi
	# find all client files and remove them
	if [ -d "/var/www/html/openWB/data/clients" ]; then
		rm /var/www/html/openWB/data/clients/*.json
		echo "Client files removed."
	else
		echo "No client files found."
	fi
} >> /var/www/html/openWB/ramdisk/reset_user_management.log 2>&1
