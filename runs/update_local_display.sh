#!/bin/bash

# update display standby timeout
if timeout=$(mosquitto_sub -p 1886 -t "openWB/optional/int_display/standby" -C 1 -W 1); then
	echo "new display timeout value: '$timeout'"
else
	echo "failed getting configured display timeout value!"
	echo "setting default value of 60s"
	timeout=60
fi
sudo sed -i "s/^xset s .*$/xset s ${timeout}/" "/home/openwb/.config/lxsession/LXDE/autostart"

# enable/disable display
default_target=$(systemctl get-default)
if display_active=$(mosquitto_sub -p 1886 -t "openWB/optional/int_display/active" -C 1 -W 1) && [[ $display_active == "true" ]]; then
	if [[ $default_target == "graphical.target" ]]; then
		echo "graphical target already configured"
	else
		echo "setting graphical target as default"
		sudo systemctl set-default graphical.target
	fi
	# only restart display manager if boot done
	if [[ -f "${OPENWBBASEDIR}/ramdisk/bootdone" ]]; then
		echo "restarting lightdm service"
		sudo systemctl restart lightdm.service
	fi
else
	if [[ $default_target == "multi-user.target" ]]; then
		echo "multi-user target already configured"
	else
		echo "setting multi-user target as default"
		sudo systemctl set-default multi-user.target
	fi
	echo "internal display not activated, stopping lightdm service if running"
	sudo systemctl stop lightdm.service
fi
