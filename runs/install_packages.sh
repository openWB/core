#!/bin/bash

echo "Installing required packages with 'apt-get'..."

# Download and install Zabbix release package if it doesn't exist
if [ ! -e zabbix-release_6.2-3+debian11_all.deb ]; then
    echo "Downloading Zabbix release package..."
    wget https://repo.zabbix.com/zabbix/6.2/raspbian/pool/main/z/zabbix-release/zabbix-release_6.2-3%2Bdebian11_all.deb
    sudo dpkg -i zabbix-release_6.2-3+debian11_all.deb
    echo "Download and installation of Zabbix release package completed."
fi

# Update package list
echo "Updating package list..."
sudo apt-get -q update

# Install required packages
echo "Installing required packages..."
sudo apt-get -q -y install \
    # Text utilities and tools
    vim bc jq socat sshpass sudo ssl-cert mmc-utils \
    # Web server and PHP
    apache2 libapache2-mod-php \
    php php-gd php-curl php-xml php-json \
    # Version control
    git \
    # MQTT tools
    mosquitto mosquitto-clients \
    # Python
    python3-pip \
    # XServer and Desktop Environment
    xserver-xorg x11-xserver-utils openbox-lxde-session lightdm lightdm-autologin-greeter accountsservice \
    # Web browser
    chromium chromium-l10n

# Install Zabbix agent and plugins
echo "Installing Zabbix agent and plugins..."
sudo apt install -y zabbix-agent2 zabbix-agent2-plugin-*

echo "Installation completed!"
