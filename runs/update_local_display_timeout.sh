#!/bin/bash
timeout=$(mosquitto_sub -p 1886 -t "openWB/optional/int_display/standby" -C 1 -W1)
if (($? == 0)); then
	echo "new display timeout value: '$timeout'"
else
	echo "failed getting configured display timeout value!"
	echo "setting default value of 60s"
	timeout=60
fi
sudo sed -i "s/^xset s .*$/xset s ${timeout}/" "/home/openwb/.config/lxsession/LXDE/autostart"
sudo systemctl restart lightdm.service
