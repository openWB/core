#!/bin/bash
echo "install required packages with 'apt-get'..."
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
if [ -z "$(dpkg -l | grep zabbix-agent2)" ]
then
    echo "install zabbix"
	wget -P /tmp/ https://repo.zabbix.com/zabbix/6.2/raspbian/pool/main/z/zabbix-release/zabbix-release_6.2-3%2Bdebian11_all.deb
	sudo dpkg -i /tmp/zabbix-release_6.2-3+debian11_all.deb
	echo "download"
	sudo apt-get -q update
	sudo apt install zabbix-agent2 zabbix-agent2-plugin-*
	sudo rm /tmp/zabbix-release_6.2-3+debian11_all.deb
fi
echo "done"
