#!/bin/bash
echo "install required packages with 'apt-get'..."
sudo apt-get -q update
sudo apt-get -q -y install \
	vim bc jq socat sshpass sudo ssl-cert mmc-utils inotify-tools \
	apache2 libapache2-mod-php \
	php php-gd php-curl php-xml php-json \
	git \
	mosquitto mosquitto-clients \
	python3-pip \
	xserver-xorg x11-xserver-utils openbox-lxde-session lightdm lightdm-autologin-greeter accountsservice \
	chromium chromium-l10n
echo "done"
