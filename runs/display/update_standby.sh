#!/bin/bash
OPENWB_BASE_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
LOGFILE="${OPENWB_BASE_DIR}/ramdisk/update_local_display.log"

# set X-Display if the script is executed via SSH or TTY
export DISPLAY="${DISPLAY:-:0}"

{
	echo "### Updating display standby settings ###"
	if timeout=$(mosquitto_sub -p 1886 -t "openWB/optional/int_display/standby" -C 1 -W 1); then
		echo "new display timeout value: ${timeout}"
		STANDBY=$timeout
	else
		echo "failed getting configured display timeout value!"
		echo "setting default value of 60s"
		STANDBY=60
	fi

	if [[ "$STANDBY" == 0 ]]; then
		# disable display standby and DPMS
		sed -i "s/^xset s .*$/xset s off\nxset -dpms/" "/home/openwb/.config/lxsession/LXDE/autostart"
		# apply display standby settings immediately
		xset s off
		xset -dpms
	else
		# set display standby timeout and enable DPMS
		sed -i "s/^xset s .*$/xset s ${STANDBY}/" "/home/openwb/.config/lxsession/LXDE/autostart"
		# apply display standby settings immediately
		xset s "$STANDBY"
		xset +dpms
	fi
} >> "$LOGFILE" 2>&1
