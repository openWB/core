#!/bin/bash
echo "install required packages with 'apt-get'..."
if [ ! -e zabbix-release_6.2-3+debian11_all.deb ]
then
	wget https://repo.zabbix.com/zabbix/6.2/raspbian/pool/main/z/zabbix-release/zabbix-release_6.2-3%2Bdebian11_all.deb
	sudo dpkg -i zabbix-release_6.2-3+debian11_all.deb
	echo "download"
fi
 sudo apt-get -q update
 sudo apt-get -q -y install \
 	vim bc jq socat sshpass sudo ssl-cert mmc-utils \
 	apache2 libapache2-mod-php \
 	php php-gd php-curl php-xml php-json \
 	git \
 	mosquitto mosquitto-clients \
 	python3-pip \
 	xserver-xorg x11-xserver-utils openbox-lxde-session lightdm lightdm-autologin-greeter accountsservice \
	chromium chromium-l10n
sudo apt install zabbix-agent2 zabbix-agent2-plugin-*
echo "done"
