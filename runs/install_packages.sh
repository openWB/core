#!/bin/bash
echo "install required packages with 'apt-get'..."
sudo apt-get update
sudo apt-get -q -y install \
	vim bc jq socat sshpass sudo ssl-cert \
	apache2 libapache2-mod-php \
	php php-gd php-curl php-xml php-json \
	git \
	mosquitto mosquitto-clients \
	python3-pip
echo "done"
