#!/bin/bash
detect_platform() {
	PLATFORM_ARCH=$(dpkg --print-architecture 2>/dev/null || echo "unknown")
	PLATFORM_KERNEL=$(uname -m)
	PLATFORM_VIRT="none"
	PLATFORM_IS_RPI=false
	PLATFORM_IS_64BIT=false
	PLATFORM_DEBIAN_VERSION=""
	PLATFORM_DEBIAN_CODENAME=""

	if [ -f /etc/os-release ]; then
		. /etc/os-release
		PLATFORM_DEBIAN_VERSION="${VERSION_ID:-unknown}"
		PLATFORM_DEBIAN_CODENAME="${VERSION_CODENAME:-unknown}"
	fi

	if command -v systemd-detect-virt >/dev/null 2>&1; then
		PLATFORM_VIRT=$(systemd-detect-virt 2>/dev/null || echo "none")
	fi

	if [ -f /proc/device-tree/model ]; then
		local model
		model=$(tr -d '\0' < /proc/device-tree/model 2>/dev/null)
		case "$model" in
			*Raspberry*Pi* | *RPI*)
				PLATFORM_IS_RPI=true
				;;
		esac
	fi

	case "$PLATFORM_KERNEL" in
		x86_64 | aarch64)
			PLATFORM_IS_64BIT=true
			;;
	esac

	PLATFORM_VENV="/opt/openwb-venv"
}

platform_has_gui() {
	if [ "$PLATFORM_IS_RPI" = true ] || [ "$PLATFORM_VIRT" = "none" ]; then
		return 0
	fi
	return 1
}

platform_install_gui_packages() {
	if platform_has_gui; then
		sudo apt-get -q -y install \
			xserver-xorg x11-xserver-utils openbox-lxde-session lightdm \
			lightdm-autologin-greeter accountsservice \
			chromium chromium-l10n 2>/dev/null || \
		sudo apt-get -q -y install \
			xserver-xorg x11-xserver-utils openbox-lxde-session lightdm \
			lightdm-autologin-greeter accountsservice
	fi
}

platform_install_rpi_packages() {
	if [ "$PLATFORM_IS_RPI" = true ]; then
		echo "Raspberry Pi detected, installing RPi-specific packages..."
		sudo apt-get -q -y install gpiozero 2>/dev/null || true
	fi
}

ensure_venv() {
	local venv_path="${1:-$PLATFORM_VENV}"
	if [ ! -f "$venv_path/bin/python3" ]; then
		echo "Creating Python virtual environment at $venv_path..."
		sudo python3 -m venv "$venv_path"
		sudo chown -R openwb:openwb "$venv_path"
		$venv_path/bin/python3 -m pip install --upgrade pip
		echo "venv created."
	else
		echo "venv already exists at $venv_path."
	fi
}

venv_pip() {
	$PLATFORM_VENV/bin/python3 -m pip "$@"
}

versionMatch() {
	local file=$1
	local target=$2
	local currentVersion
	local installedVersion
	currentVersion=$(grep -o "openwb-version:[0-9]\+" "$file" 2>/dev/null | grep -o "[0-9]\+$")
	if [ -r "$target" ]; then
		installedVersion=$(grep -o "openwb-version:[0-9]\+" "$target" 2>/dev/null | grep -o "[0-9]\+$")
	else
		installedVersion=$(sudo grep -o "openwb-version:[0-9]\+" "$target" 2>/dev/null | grep -o "[0-9]\+$")
	fi
	if [[ -n "$currentVersion" ]] && [[ "$currentVersion" == "$installedVersion" ]]; then
		return 0
	else
		return 1
	fi
}
