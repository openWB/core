#!/bin/bash
echo "add required repositories..."
# add mosquitto repository
if [ ! -f /etc/apt/sources.list.d/mosquitto.list ]; then
	sudo apt-get -q -y install wget apt-transport-https
	sudo wget -q https://repo.mosquitto.org/debian/mosquitto-repo.gpg -O /etc/apt/trusted.gpg.d/mosquitto-repo.gpg
	# get installed debian version
	. /etc/os-release
	sudo wget -q -O /etc/apt/sources.list.d/mosquitto.list "https://repo.mosquitto.org/debian/mosquitto-${VERSION_CODENAME}.list"
fi
echo "done"

echo "install required packages with 'apt-get'..."
sudo apt-get -q update
sudo apt-get -q -y install \
	vim bc jq curl socat sshpass sudo ssl-cert mmc-utils inotify-tools iptables \
	build-essential make libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev libffi-dev liblzma-dev xz-utils tk-dev libncursesw5-dev \
	apache2 libapache2-mod-php \
	php php-gd php-curl php-xml php-json \
	git \
	mosquitto mosquitto-clients \
	xserver-xorg x11-xserver-utils openbox-lxde-session lightdm lightdm-autologin-greeter accountsservice \
	chromium chromium-l10n
echo "done"
