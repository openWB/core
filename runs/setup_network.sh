#!/bin/bash
OPENWBBASEDIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

dhcpcd_config_source="${OPENWBBASEDIR}/data/config/dhcpcd.conf"
dhcpcd_config_target="/etc/dhcpcd.conf"

dnsmasq_config_source="${OPENWBBASEDIR}/data/config/dnsmasq.conf"
dnsmasq_config_target="/etc/dnsmasq.conf"

function versionMatch() {
	file=$1
	target=$2
	currentVersion=$(grep -o "openwb-version:[0-9]\+" "$file" | grep -o "[0-9]\+$")
	installedVersion=$(grep -o "openwb-version:[0-9]\+" "$target" | grep -o "[0-9]\+$")
	if ((currentVersion == installedVersion)); then
		return 0
	else
		return 1
	fi
}

function update_file() {
	file=$1
	target=$2
	if versionMatch "$file" "$target"; then
		echo "$target is up to date"
		return 0
	else
		sudo cp "$file" "$target"
		return 1
	fi
}

function get_primary_interface() {
	myPrimaryNetDevice=$(ip route get 1 | awk '{print $5;exit}')
	echo "$myPrimaryNetDevice"
}

function get_ip() {
	ip="$(ip route get 1 | awk '{print $7;exit}')"
	if [[ $ip == "" ]]; then
		ip="unknown"
	fi
	echo "$ip"
}

function get_mac() {
	mac=$(ip addr show "$(get_primary_interface)" | grep "ether" | cut -d " " -f 6)
	echo "$mac"
}

function setup_pnp_network() {
	# ToDo: make ip configurable
	myVirtualIp="192.168.193.250"
	isSecondary=$(mosquitto_sub -t "openWB/general/extern" -p 1886 -C 1 -W 1 --quiet)
	if [[ $isSecondary == "true" ]]; then
		echo "running as secondary, disabling plug'n'play network on dev $myPrimaryNetDevice"
		sudo ip addr del "$myVirtualIp/24" dev "$myPrimaryNetDevice"
	else
		echo "running as primary, enabling plug'n'play network on dev $myPrimaryNetDevice"
		sudo ip addr add "$myVirtualIp/24" dev "$myPrimaryNetDevice"
	fi
}

function check_internet_connection() {
	if curl -s --head  --request GET "https://www.github.com" >/dev/null; then
		echo "Internet connection is up"
	else
		echo "ERROR: no internet connection!"
		exit 1
	fi
}

function setup_dnsmasq() {
	sudo apt-get install -y dnsmasq
	if update_file "$dnsmasq_config_source" "$dnsmasq_config_target"; then
		echo "restarting dnsmasq"
		sudo systemctl restart dnsmasq
	fi
}

function disable_dnsmasq() {
	sudo systemctl stop dnsmasq
	sudo systemctl disable dnsmasq
}

function setup_dhcpcd_proplus() {
	echo "checking dhcpcd.conf..."
	if versionMatch "$dhcpcd_config_source" "$dhcpcd_config_target"; then
		echo "no changes required"
	else
		echo "openwb section not found or outdated"
		# delete old settings with version tag
		pattern_begin=$(grep -m 1 '#' "$dhcpcd_config_source")
		pattern_end=$(grep '#' "$dhcpcd_config_source" | tail -n 1)
		sudo sed -i "/$pattern_begin/,/$pattern_end/d" "$dhcpcd_config_target"
		# add new settings
		echo "adding dhcpcd settings to $dhcpcd_config_target..."
		sudo tee -a "$dhcpcd_config_target" <"$dhcpcd_config_source" >/dev/null
		echo "done"
		echo "restarting dhcpcd"
		sudo systemctl restart dhcpcd
	fi
}

function disable_dhcpcd_proplus() {
	echo "checking dhcpcd.conf..."
	if versionMatch "$dhcpcd_config_source" "$dhcpcd_config_target"; then
		echo "openwb section found, deleting..."
		# delete old settings with version tag
		pattern_begin=$(grep -m 1 '#' "$dhcpcd_config_source")
		pattern_end=$(grep '#' "$dhcpcd_config_source" | tail -n 1)
		sudo sed -i "/$pattern_begin/,/$pattern_end/d" "$dhcpcd_config_target"
		echo "restarting dhcpcd"
		sudo systemctl restart dhcpcd
	else
		echo "no changes required"
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

# publish mac address
mac="$(get_mac)"
mosquitto_pub -t "openWB/system/mac_address" -p 1886 -r -m "\"$mac\""

# image restricted to LAN only
# get local ip
ip="$(get_ip)"
echo "my primary IP: $ip"
mosquitto_pub -t "openWB/system/ip_address" -p 1886 -r -m "\"$ip\""
myPrimaryNetDevice=$(get_primary_interface)
echo "my primary interface: $myPrimaryNetDevice"
setup_pnp_network
if ! check_internet_connection; then
	exit 1
fi

# check for pro plus
echo "ProPlus..."
if lsusb | grep -q 'RTL8153'; then
	echo "second network for pro plus detected"
	setup_dnsmasq
	setup_dhcpcd_proplus
	sudo sysctl net.ipv4.ip_forward=1
	sudo iptables -t nat -A POSTROUTING -o "$myPrimaryNetDevice" -j MASQUERADE

else
	echo "no second network for pro plus detected"
	disable_dnsmasq
	disable_dhcpcd_proplus
	sudo iptables -t nat -D POSTROUTING -o "$myPrimaryNetDevice" -j MASQUERADE
	sudo sysctl net.ipv4.ip_forward=0
fi
