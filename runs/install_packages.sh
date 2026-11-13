#!/bin/bash
. /etc/os-release

echo "install required packages with 'apt-get'..."
python_build_packages=()
python_binary_packages=()
case $(dpkg --print-architecture) in
	arm64) python_binary_packages=(python3-evdev) ;;
	arm*) ;;
	*) python_build_packages=(gcc python3-dev) ;;
esac
if ! sudo apt-get -q -o APT::Update::Error-Mode=any update; then
	echo "Failed to refresh package indexes; aborting package installation" >&2
	exit 1
fi
if ! sudo apt-get -q -y install \
	vim bc jq curl socat sshpass sudo ssl-cert mmc-utils inotify-tools iptables systemd-zram-generator \
	apache2 libapache2-mod-php \
	php php-gd php-curl php-xml php-json \
	git \
	mosquitto mosquitto-clients \
	python3-pip \
	python3-venv \
	"${python_build_packages[@]}" \
	"${python_binary_packages[@]}"; then
	echo "Failed to install required system packages" >&2
	exit 1
fi
echo "done"
