#!/bin/bash
echo "check if zabbix agent is already installed..."
if [ -z "$(dpkg -l | grep zabbix-agent2)" ]; then
	echo "start download..."
	wget -P /tmp/ https://repo.zabbix.com/zabbix/6.2/raspbian/pool/main/z/zabbix-release/zabbix-release_6.2-3%2Bdebian11_all.deb
	sudo dpkg -i /tmp/zabbix-release_6.2-3+debian11_all.deb
	echo "install zabbix."
	sudo apt-get -q update
	sudo apt-get install zabbix-agent2 zabbix-agent2-plugin-*
	sudo rm /tmp/zabbix-release_6.2-3+debian11_all.deb
else
	echo "nothing to do."
fi
echo "done"
