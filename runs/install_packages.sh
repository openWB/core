#!/bin/bash
echo "install required packages with 'apt-get'..."
sudo apt-get update
sudo apt-get -q -y install \
	vim \
	bc \
	apache2 libapache2-mod-php \
	php php-gd php-curl php-xml php-json \
	jq \
	git \
	mosquitto mosquitto-clients \
	socat \
	python3-pip \
	sshpass \
	sudo \
	xserver-xorg x11-xserver-utils openbox-lxde-session lightdm lightdm-autologin-greeter accountsservice \
	chromium chromium-l10n
echo "done"
