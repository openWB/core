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
		echo "running as secondary, disabling plug'n'play network on dev $myNetDevice"
		sudo ip addr del "$myVirtualIp/24" dev $myNetDevice
	else
		echo "running as primary, enabling plug'n'play network on dev $myNetDevice"
		sudo ip addr add "$myVirtualIp/24" dev $myNetDevice
	fi
}

function check_internet_connection() {
	if ping -c1 "www.openwb.de" &>/dev/null; then
		echo "Internet connection is up"
	else
		echo "ERROR: no internet connection!"
		exit 1
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
if ((connectCounter >= 30)); then
	echo "ERROR: network not up after $connectCounter seconds!"
	exit 1
fi

# image restricted to LAN only
# get local ip
ip="$(get_ip)"
echo "my primary IP: $ip"
mosquitto_pub -t "openWB/system/ip_address" -p 1886 -r -m "\"$ip\""
setup_pnp_network
if ! check_internet_connection; then
	exit 1
fi
