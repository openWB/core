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
} >> /var/www/html/openWB/ramdisk/reset_user_management.log 2>&1
