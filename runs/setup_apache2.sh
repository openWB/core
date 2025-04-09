#!/bin/bash
OPENWBBASEDIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
restartService=0

versionMatch() {
	file=$1
	target=$2
	currentVersion=$(grep -o "openwb-version:[0-9]\+" "$file" | grep -o "[0-9]\+$")
	installedVersion=$(grep -o "openwb-version:[0-9]\+" "$target" | grep -o "[0-9]\+$")
	if ((currentVersion == installedVersion)); then
		return 0
	else
		return 1
	fi
}

updateFile() {
	file=$1
	target=$2
	if versionMatch "$file" "$target"; then
		echo "$target is up to date"
	else
		sudo cp "$file" "$target"
		restartService=1
	fi
}

enableModule() {
	module=$1
	if sudo a2query -m "$module" -q; then
		echo "module '$module' already enabled"
	else
		echo "module '$module' currently disabled; enabling module"
		sudo a2enmod "$module"
		restartService=1
	fi
}

disableModule() {
	module=$1
	if sudo a2query -m "$module" -q; then
		echo "module '$module' currently enabled; disabling module"
		sudo a2dismod "$module"
		restartService=1
	else
		echo "module '$module' already disabled"
	fi
}

enableSite() {
	site=$1
	if sudo a2query -s "$site" -q; then
		echo "site '$site' already enabled"
	else
		echo "site '$site' currently disabled; enabling site"
		sudo a2ensite "$site"
		restartService=1
	fi
}

disableSite() {
	site=$1
	if sudo a2query -s "$site" -q; then
		echo "site '$site' currently enabled; disabling site"
		sudo a2dissite "$site"
		restartService=1
	else
		echo "site '$site' already disabled"
	fi
}

# check apache modules
echo "checking required apache modules..."
enableModule headers
enableModule ssl
enableModule proxy_wstunnel

# default site (http and https)
echo "apache default site..."
updateFile "${OPENWBBASEDIR}/data/config/apache/000-default.conf" "/etc/apache2/sites-available/000-default.conf"
echo "apache default ssl site..."
updateFile "${OPENWBBASEDIR}/data/config/apache/apache-openwb-ssl.conf" "/etc/apache2/sites-available/apache-openwb-ssl.conf"
# http api site (https only)
echo "apache http api ssl site..."
updateFile "${OPENWBBASEDIR}/data/config/apache/http-api-ssl.conf" "/etc/apache2/sites-available/http-api-ssl.conf"
# proplus site 
echo "apache pro plus site..."
updateFile "${OPENWBBASEDIR}/data/config/apache/apache-proplus.conf" "/etc/apache2/sites-available/apache-proplus.conf"

# disable apache default ssl site
disableSite default-ssl
# enable openwb ssl site
enableSite apache-openwb-ssl
# enable http api ssl site if configured
httpApiEnabled=$(mosquitto_sub -t "openWB/general/http_api" -p 1886 -C 1 -W 1 --quiet)
if [[ $httpApiEnabled == "true" ]]; then
	echo "http api is enabled"
	enableSite http-api-ssl
else
	echo "http api is disabled"
	disableSite http-api-ssl
fi

# check for pro+
echo "Pro+ setup..."
if lsusb | grep -q 'RTL8153'; then
	echo "second network for pro plus detected"
	# enable pro+ specific configurations
	enableModule proxy_http
	# enableModule proxy_fcgi
	# enableModule proxy_ajp
	enableSite apache-proplus
else
	echo "no second network for pro plus detected"
	# disable all pro+ specific configurations
	disableModule proxy_http
	# disableModule proxy_fcgi
	# disableModule proxy_ajp
	disableSite apache-proplus
fi

# restart apache if required
if ((restartService == 1)); then
	echo -n "restarting apache..."
	sudo systemctl restart apache2
	echo "done"
else
	echo "apache configuration is already up to date"
fi
