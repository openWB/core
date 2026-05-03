#!/bin/bash
OPENWBBASEDIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
source "${OPENWBBASEDIR}/runs/platform_detect.sh"
detect_platform

echo "=== Platform Detection ==="
echo "  Architecture:  $PLATFORM_ARCH ($PLATFORM_KERNEL)"
echo "  Debian:        $PLATFORM_DEBIAN_VERSION ($PLATFORM_DEBIAN_CODENAME)"
echo "  Virtualization: $PLATFORM_VIRT"
echo "  Raspberry Pi:  $PLATFORM_IS_RPI"
echo "  64-bit:        $PLATFORM_IS_64BIT"
echo "==========================="

echo "add required repositories..."
if [ ! -f /etc/apt/sources.list.d/mosquitto.list ]; then
	sudo apt-get -q -y install wget apt-transport-https
	sudo wget -q https://repo.mosquitto.org/debian/mosquitto-repo.gpg -O /etc/apt/trusted.gpg.d/mosquitto-repo.gpg
	sudo wget -q -O /etc/apt/sources.list.d/mosquitto.list \
		"https://repo.mosquitto.org/debian/mosquitto-${PLATFORM_DEBIAN_CODENAME}.list"
fi
echo "done"

echo "install required packages with 'apt-get'..."
sudo apt-get -q update

COMMON_PACKAGES=(
	vim bc jq curl socat sshpass sudo ssl-cert inotify-tools iptables
	caddy php-fpm
	php php-gd php-curl php-xml php-json
	git
	mosquitto mosquitto-clients
	python3 python3-venv python3-dev gcc linux-headers-$(uname -r)
	chrony
)

if [ "$PLATFORM_IS_RPI" = true ]; then
	COMMON_PACKAGES+=(mmc-utils)
fi

sudo apt-get -q -y install "${COMMON_PACKAGES[@]}"
echo "base packages done"

platform_install_rpi_packages

platform_install_gui_packages

echo "done"
