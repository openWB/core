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
	apache2 libapache2-mod-php \
	php php-gd php-curl php-xml php-json \
	git \
	mosquitto mosquitto-clients \
	python3-pip \
	python3-urllib3 \
	xserver-xorg x11-xserver-utils openbox-lxde-session lightdm lightdm-autologin-greeter accountsservice \
	chromium chromium-l10n
echo "done"

# Apply the PHP 7.4 package fix for php2shell on supported Debian 11 platforms.
. /etc/os-release
php74_fix_url=""
if [ "${VERSION_ID:-}" = "11" ] && [ "$(dpkg --print-architecture)" = "armhf" ] && [ "${ID:-}" = "raspbian" ]; then
	php74_fix_url="https://openwb.de/update/openwb-php74-fix-r2-raspbian11-armhf.tar.xz"
elif [ "${VERSION_ID:-}" = "11" ] && [ "$(dpkg --print-architecture)" = "amd64" ] && [ "${ID:-}" = "debian" ]; then
	php74_fix_url="https://openwb.de/update/openwb-php74-fix-r2-debian11-amd64.tar.xz"
fi

php74_fix_needed=$(dpkg-query -W -f='${db:Status-Status} ${Version}\n' \
	php7.4-cli php7.4-common libapache2-mod-php7.4 2>/dev/null |
	awk '$1 == "installed" && index($2, "+owphp2shell1") == 0 { needed = 1 } END { print needed + 0 }')

if [ -n "$php74_fix_url" ] && [ "$php74_fix_needed" -eq 1 ]; then
	(
		set -e
		workdir=$(mktemp -d "$HOME/php-fix-r2.XXXXXX")
		apache_stopped=0
		restart_apache() {
			if [ "$apache_stopped" -eq 1 ]; then
				sudo systemctl start apache2 || true
			fi
		}
		cleanup() {
			restart_apache
			rm -rf "$workdir"
		}
		trap cleanup EXIT

		echo "Applying PHP 7.4 package fix..."
		curl -fL -o "$workdir/php74-fix.tar.xz" "$php74_fix_url"
		tar -xf "$workdir/php74-fix.tar.xz" -C "$workdir"
		package_dir=$(find "$workdir" -mindepth 1 -maxdepth 2 -type f -name SHA256SUMS -printf '%h\n' -quit)
		if [ -z "$package_dir" ] || [ ! -d "$package_dir/pakete" ]; then
			echo "PHP 7.4 package archive has an unexpected structure." >&2
			exit 1
		fi
		cd "$package_dir"
		sha256sum -c SHA256SUMS
		sudo apt-get --simulate --no-remove install -y ./pakete/*.deb
		apache_stopped=1
		sudo systemctl stop apache2
		sudo apt-get --no-remove install -y ./pakete/*.deb
		sudo apache2ctl configtest
		sudo systemctl start apache2
		apache_stopped=0
		dpkg-query -W php7.4-cli php7.4-common libapache2-mod-php7.4
		status=$(sudo systemctl is-active "apache2" || true)
		printf 'apache2: %s\n' "$status"
	) || {
		echo "PHP 7.4 package fix failed." >&2
		exit 1
	}
elif [ -n "$php74_fix_url" ] && [ "$php74_fix_needed" -eq 0 ]; then
	echo "PHP 7.4 package fix for php2shell is already applied."
elif [ -z "$php74_fix_url" ]; then
	echo "PHP 7.4 package fix for php2shell is not supported on this platform."
fi
