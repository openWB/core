#!/bin/bash

function get_primary_interface() {
	myNetDevice=$(ip route get 1 | awk '{print $5;exit}')
	echo "$myNetDevice"
}

function get_ip() {
	ip="$(ip route get 1 | awk '{print $7;exit}')"
	if [[ $ip == "" ]]; then
		ip="unknown"
	fi
	echo "$ip"
}

function setup_pnp_network() {
	# ToDo: make ip configurable
	myVirtualIp="192.168.193.250"
	myNetDevice=$(get_primary_interface)
	echo "my primary interface: $myNetDevice"
	isSecondary=$(mosquitto_sub -t "openWB/general/extern" -p 1886 -C 1 -W 1 --quiet)
	if [[ $isSecondary == "true" ]]; then
		echo "running as secondary, disabling plug'n'play network"
		sudo ifconfig "${myNetDevice}:0" down
	else
		echo "running as primary, enabling plug'n'play network"
		sudo ifconfig "${myNetDevice}:0" "$myVirtualIp" netmask 255.255.255.0 up
	fi
}

# check for LAN/WLAN connection
echo -n "Wait for connection..."
connectCounter=0
while [[ ! $(ip route get 1) ]] && ((connectCounter < 30)); do
	((connectCounter += 1))
	echo -n "."
	sleep 1
done
echo ""
if ((connectCounter <30)); then
	# image restricted to LAN only
	# get local ip
	ip="$(get_ip)"
	echo "my primary IP: $ip"
	mosquitto_pub -t "openWB/system/ip_address" -p 1886 -r -m "\"$ip\""
	setup_pnp_network
else
	echo "ERROR: network not up after $connectCounter seconds!"
fi
