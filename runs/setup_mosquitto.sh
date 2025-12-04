#!/bin/bash
OPENWBBASEDIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
automaticServiceRestart=${1:-0}

versionMatch() {
	file=$1
	target=$2
	currentVersion=$(grep -o "openwb-version:[0-9]\+" "$file" | grep -o "[0-9]\+$")
	installedVersion=$(sudo grep -o "openwb-version:[0-9]\+" "$target" | grep -o "[0-9]\+$")
	if ((currentVersion == installedVersion)); then
		return 0
	else
		return 1
	fi
}

waitForServiceStop() {
	# this function waits for a service to stop and kills the process if it takes too long
	# this is necessary at least for mosquitto, as the service is stopped, but the process is still running
	service=$1
	pattern=$2
	timeout=$3

	counter=0
	sudo systemctl stop "$service"
	while pgrep --full "$pattern" >/dev/null && ((counter < timeout)); do
		echo "process '$pattern' still running after ${counter}s, waiting..."
		sleep 1
		((counter++))
	done
	if ((counter >= timeout)); then
		echo "process '$pattern' still running after ${timeout}s, killing process"
		sudo pkill --full "$pattern" --signal 9
		sleep 2
		# if the process was killed, the service is in "active (exited)" state
		# so we need to trigger a stop here to be able to start it again
		sudo systemctl stop "$service"
	fi
}

# check for mosquitto configuration
echo "check mosquitto installation..."
restartService=0
SRC="${OPENWBBASEDIR}/data/config/mosquitto/public"

echo "mosquitto main configuration..."
if versionMatch "${SRC}/mosquitto.conf" "/etc/mosquitto/mosquitto.conf"; then
	echo "mosquitto.conf already up to date"
else
	echo "updating mosquitto.conf"
	sudo cp "${SRC}/mosquitto.conf" "/etc/mosquitto/mosquitto.conf"
	restartService=1
fi

echo "mosquitto openwb configuration..."
if versionMatch "${SRC}/openwb.conf" "/etc/mosquitto/conf.d/openwb.conf"; then
	echo "mosquitto openwb.conf already up to date"
else
	echo "updating mosquitto openwb.conf"
	sudo cp "${SRC}/openwb.conf" "/etc/mosquitto/conf.d/openwb.conf"
	restartService=1
fi

userManagementActive=$(mosquitto_sub -t "openWB/general/user_management_active" -p 1886 -C 1 -W 1 --quiet)
allowUnencryptedAccess=$(mosquitto_sub -t "openWB/general/allow_unencrypted_access" -p 1886 -C 1 -W 1 --quiet)
echo "mosquitto settings: user_management_active=$userManagementActive, allow_unencrypted_access=$allowUnencryptedAccess"
if [[ $userManagementActive == "true" ]]; then
	echo "mosquitto user management enabled, disabling unencrypted access"
	allowUnencryptedAccess="false"
	if versionMatch "${SRC}/openwb-user-management.conf" "/etc/mosquitto/conf.d/openwb-user-management.conf"; then
		echo "mosquitto openwb-user-management.conf already up to date"
	else
		echo "updating mosquitto openwb-user-management.conf"
		sudo cp "${SRC}/openwb-user-management.conf" "/etc/mosquitto/conf.d/openwb-user-management.conf"
		restartService=1
	fi
	if [ -f "/var/lib/mosquitto/dynamic-security.json" ]; then
		echo "dynamic security configuration found, no action needed"
	else
		echo "creating initial dynamic security configuration with default user 'admin' and password 'openwb'"
		sudo cp "${SRC}/default-dynamic-security.json" /var/lib/mosquitto/dynamic-security.json
		sudo chown mosquitto:mosquitto /var/lib/mosquitto/dynamic-security.json
		cp "${SRC}/mosquitto_ctrl" /home/openwb/.config/mosquitto_ctrl
		restartService=1
	fi
	if [ -f "/etc/mosquitto/conf.d/openwb-default-acl.conf" ]; then
		echo "removing mosquitto openwb-default-acl.conf"
		sudo rm "/etc/mosquitto/conf.d/openwb-default-acl.conf"
		restartService=1
	else
		echo "mosquitto openwb-default-acl.conf not present, no action needed"
	fi
	if [ -f "/etc/mosquitto/conf.d/openwb-unsecure-acl.conf" ]; then
		echo "removing mosquitto openwb-unsecure-acl.conf"
		sudo rm "/etc/mosquitto/conf.d/openwb-unsecure-acl.conf"
		restartService=1
	else
		echo "mosquitto openwb-unsecure-acl.conf not present, no action needed"
	fi
else
	if [ -f "/etc/mosquitto/conf.d/openwb-user-management.conf" ]; then
		sudo rm "/etc/mosquitto/conf.d/openwb-user-management.conf"
		restartService=1
	fi
	if versionMatch "${SRC}/openwb-default-acl.conf" "/etc/mosquitto/conf.d/openwb-default-acl.conf"; then
		echo "mosquitto openwb-default-acl.conf already up to date"
	else
		echo "updating mosquitto openwb-default-acl.conf"
		sudo cp "${SRC}/openwb-default-acl.conf" "/etc/mosquitto/conf.d/openwb-default-acl.conf"
		restartService=1
	fi
fi
if [[ $allowUnencryptedAccess == "true" ]]; then
	if versionMatch "${SRC}/openwb-unsecure-acl.conf" "/etc/mosquitto/conf.d/openwb-unsecure-acl.conf"; then
		echo "mosquitto openwb-unsecure-acl.conf already up to date"
	else
		echo "updating mosquitto openwb-unsecure-acl.conf"
		sudo cp "${SRC}/openwb-unsecure-acl.conf" "/etc/mosquitto/conf.d/openwb-unsecure-acl.conf"
		restartService=1
	fi
else
	if [ -f "/etc/mosquitto/conf.d/openwb-unsecure-acl.conf" ]; then
		echo "removing mosquitto openwb-unsecure-acl.conf"
		sudo rm "/etc/mosquitto/conf.d/openwb-unsecure-acl.conf"
		restartService=1
	else
		echo "mosquitto openwb-unsecure-acl.conf not present, no action needed"
	fi
fi

echo "mosquitto acl configuration..."
if versionMatch "${SRC}/mosquitto.acl" "/etc/mosquitto/mosquitto.acl"; then
	echo "mosquitto acl already up to date"
else
	echo "updating mosquitto acl"
	sudo cp "${SRC}/mosquitto.acl" "/etc/mosquitto/mosquitto.acl"
	sudo chown mosquitto:mosquitto "/etc/mosquitto/mosquitto.acl"
	restartService=1
fi

echo "mosquitto certificates..."
if [[ ! -f "/etc/mosquitto/certs/openwb.key" ]]; then
	echo -n "copy ssl certs..."
	sudo cp "/etc/ssl/certs/ssl-cert-snakeoil.pem" "/etc/mosquitto/certs/openwb.pem"
	sudo cp "/etc/ssl/private/ssl-cert-snakeoil.key" "/etc/mosquitto/certs/openwb.key"
	sudo chgrp mosquitto "/etc/mosquitto/certs/openwb.key"
	restartService=1
	echo "done"
fi
if ((restartService == 1 && automaticServiceRestart == 1)); then
	echo -n "restarting mosquitto service..."
	waitForServiceStop "mosquitto" "mosquitto.conf" 10
	sudo systemctl start mosquitto
	echo "done"
fi

#check for mosquitto_local instance
# restartService=0  # if we restart mosquitto, we need to restart mosquitto_local as well
SRC="${OPENWBBASEDIR}/data/config/mosquitto/local"
echo "mosquitto_local instance..."
if versionMatch "${SRC}/mosquitto_local_init" "/etc/init.d/mosquitto_local"; then
	echo "mosquitto_local service definition already up to date"
else
	echo "updating mosquitto_local service definition"
	sudo cp "${SRC}/mosquitto_local_init" /etc/init.d/mosquitto_local
	sudo chown root:root /etc/init.d/mosquitto_local
	sudo chmod 755 /etc/init.d/mosquitto_local
	sudo systemctl daemon-reload
	sudo systemctl enable mosquitto_local
	restartService=1
fi
if versionMatch "${SRC}/mosquitto_local.conf" "/etc/mosquitto/mosquitto_local.conf"; then
	echo "mosquitto_local.conf already up to date"
else
	echo "updating mosquitto_local.conf"
	sudo cp -a "${SRC}/mosquitto_local.conf" "/etc/mosquitto/mosquitto_local.conf"
	restartService=1
fi
if versionMatch "${SRC}/openwb_local.conf" "/etc/mosquitto/conf_local.d/openwb_local.conf"; then
	echo "mosquitto openwb_local.conf already up to date"
else
	echo "updating mosquitto openwb_local.conf"
	sudo cp -a "${SRC}/openwb_local.conf" "/etc/mosquitto/conf_local.d/"
	restartService=1
fi
if ((restartService == 1 && automaticServiceRestart == 1)); then
	echo -n "restarting mosquitto_local service..."
	waitForServiceStop "mosquitto_local" "mosquitto_local.conf" 10
	sudo systemctl start mosquitto_local
	echo "done"
fi
echo "mosquitto done"
