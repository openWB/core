#!/bin/bash
set -e

OPENWBBASEDIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

if (( EUID != 0 )); then
	exec sudo bash "${BASH_SOURCE[0]}" "$@"
fi

# Do not change systems using dhcpcd, networkd or another time service.
if ! command -v nmcli >/dev/null || ! systemctl is-active --quiet NetworkManager.service ||
	! systemctl is-active --quiet systemd-timesyncd.service; then
	echo "NetworkManager/timesyncd not active, skipping DHCP NTP integration"
	exit 0
fi

source_file="${OPENWBBASEDIR}/data/config/networkmanager/60-openwb-ntp"
dispatcher="/etc/NetworkManager/dispatcher.d/60-openwb-ntp"

install -d -o root -g root -m 0755 /etc/NetworkManager/dispatcher.d
if ! cmp -s "$source_file" "$dispatcher"; then
	install -o root -g root -m 0755 "$source_file" "$dispatcher"
	echo "installed NetworkManager DHCP NTP dispatcher"
fi
# NetworkManager ignores dispatchers with unsafe ownership or permissions.
chown root:root "$dispatcher"
chmod 0755 "$dispatcher"

# The connection may already be up before the dispatcher is installed.
"$dispatcher" none refresh
