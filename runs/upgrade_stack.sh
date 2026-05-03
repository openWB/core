#!/bin/bash
OPENWBBASEDIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
source "${OPENWBBASEDIR}/runs/platform_detect.sh"
detect_platform

UPGRADE_MARKER="${OPENWBBASEDIR}/.stack-version"
CURRENT_STACK=3

needs_upgrade() {
	if [ ! -f "$UPGRADE_MARKER" ]; then
		return 0
	fi
	local marker_version
	marker_version=$(cat "$UPGRADE_MARKER" 2>/dev/null)
	if [[ "$marker_version" != "$CURRENT_STACK" ]]; then
		return 0
	fi
	return 1
}

is_python_supported() {
	local py_bin="${1:-python3}"
	local major minor
	major=$($py_bin -c 'import sys; print(sys.version_info.major)' 2>/dev/null)
	minor=$($py_bin -c 'import sys; print(sys.version_info.minor)' 2>/dev/null)
	if [[ "$major" -ge 3 && "$minor" -ge 10 ]]; then
		return 0
	fi
	return 1
}

get_python_version() {
	$1 -c 'import sys; print("{}.{}".format(sys.version_info.major, sys.version_info.minor))' 2>/dev/null
}

# --- Main upgrade logic ---

echo "=== openWB Stack Upgrade Check ==="
echo "  OS: Debian $PLATFORM_DEBIAN_VERSION ($PLATFORM_DEBIAN_CODENAME)"
echo "  Arch: $PLATFORM_ARCH ($PLATFORM_KERNEL)"
echo "  Virtualization: $PLATFORM_VIRT"
echo "  Raspberry Pi: $PLATFORM_IS_RPI"
echo "==================================="

if ! needs_upgrade; then
	echo "Stack is up to date (version $CURRENT_STACK). No upgrade needed."
	exit 0
fi

echo "Stack upgrade required (target: version $CURRENT_STACK). Starting upgrade..."

# --- Step 1: Enable backports on Bookworm ---
if [[ "$PLATFORM_DEBIAN_CODENAME" == "bookworm" ]]; then
	echo ""
	echo "--- Step 1: Enabling bookworm-backports ---"
	if ! grep -q "bookworm-backports" /etc/apt/sources.list /etc/apt/sources.list.d/*.sources 2>/dev/null; then
		if [ -f /etc/apt/sources.list.d/debian.sources ]; then
			if ! grep -q "bookworm-backports" /etc/apt/sources.list.d/debian.sources; then
				echo "Adding backports to DEB822 sources..."
				sudo sed -i '/^URIs:.*\/debian$/ { N; /\nSuites:.*bookworm-updates/ s/\(Suites: .*\)/\1 bookworm-backports/ }' /etc/apt/sources.list.d/debian.sources
			fi
		else
			echo "Adding backports to traditional sources.list..."
			if ! grep -q "bookworm-backports" /etc/apt/sources.list; then
				echo "deb http://deb.debian.org/debian bookworm-backports main" | sudo tee -a /etc/apt/sources.list > /dev/null
			fi
		fi
		echo "Updating package lists..."
		sudo apt-get -q update 2>/dev/null
	else
		echo "Backports already enabled."
	fi
else
	echo "--- Step 1: Not Bookworm, skipping backports setup ---"
fi

# --- Step 2: Determine and install Python ---
echo ""
echo "--- Step 2: Python installation ---"

PYTHON_TARGET=""
PYTHON_BIN=""

# Check available Python versions - prefer 3.13, fall back to 3.12, then 3.11+
for py_ver in 3.13 3.12 3.11 3.10; do
	py_bin="/usr/bin/python${py_ver}"
	if [ -x "$py_bin" ]; then
		if is_python_supported "$py_bin"; then
			PYTHON_BIN="$py_bin"
			PYTHON_TARGET="$py_ver"
			echo "Found system Python $py_ver: $($py_bin --version 2>/dev/null)"
			break
		fi
	fi
done

if [ -z "$PYTHON_BIN" ]; then
	echo "No supported Python (>=3.10) found. Installing..."
	if [[ "$PLATFORM_DEBIAN_CODENAME" == "bookworm" ]]; then
		echo "Trying python3.13 from bookworm-backports..."
		sudo apt-get -q -y install -t bookworm-backports python3.13 python3.13-venv python3.13-dev 2>/dev/null
		if [ -x /usr/bin/python3.13 ]; then
			PYTHON_BIN="/usr/bin/python3.13"
			PYTHON_TARGET="3.13"
		else
			echo "python3.13 not available in backports, trying python3.12..."
			sudo apt-get -q -y install -t bookworm-backports python3.12 python3.12-venv python3.12-dev 2>/dev/null
			if [ -x /usr/bin/python3.12 ]; then
				PYTHON_BIN="/usr/bin/python3.12"
				PYTHON_TARGET="3.12"
			fi
		fi
	fi

	if [ -z "$PYTHON_BIN" ]; then
		echo "Installing default python3 + venv + dev..."
		sudo apt-get -q -y install python3 python3-venv python3-dev
		if is_python_supported /usr/bin/python3; then
			PYTHON_BIN="/usr/bin/python3"
			PYTHON_TARGET="python3"
		fi
	fi
fi

if [ -z "$PYTHON_BIN" ]; then
	echo "ERROR: No Python >= 3.10 available! Cannot continue."
	echo "This system needs manual intervention."
	exit 1
fi

echo "Using Python: $PYTHON_BIN ($(get_python_version $PYTHON_BIN))"

# --- Step 3: Create / update virtual environment ---
echo ""
echo "--- Step 3: Virtual environment ---"

VENV_PATH="$PLATFORM_VENV"
VENV_PYTHON_VERSION=""
if [ -f "$VENV_PATH/bin/python3" ]; then
	VENV_PYTHON_VERSION=$($VENV_PATH/bin/python3 -c 'import sys; print("{}.{}".format(sys.version_info.major, sys.version_info.minor))' 2>/dev/null)
fi

VENV_NEEDS_RECREATE=0
if [ ! -f "$VENV_PATH/bin/python3" ]; then
	VENV_NEEDS_RECREATE=1
	echo "No venv found, will create."
elif ! is_python_supported "$VENV_PATH/bin/python3"; then
	VENV_NEEDS_RECREATE=1
	echo "Venv has Python $VENV_PYTHON_VERSION (< 3.10), needs recreation."
fi

if [[ "$VENV_NEEDS_RECREATE" == "1" ]]; then
	echo "Creating venv with $PYTHON_BIN at $VENV_PATH..."
	if [ -d "$VENV_PATH" ]; then
		echo "Removing old venv..."
		sudo rm -rf "$VENV_PATH"
	fi
	sudo $PYTHON_BIN -m venv "$VENV_PATH"
	sudo chown -R openwb:openwb "$VENV_PATH"
	$VENV_PATH/bin/python3 -m pip install --upgrade pip
	echo "Venv created with Python $($VENV_PATH/bin/python3 --version 2>/dev/null)"
else
	echo "Venv already exists with Python $VENV_PYTHON_VERSION, OK."
fi

# --- Step 4: Web server migration (Apache -> Caddy + PHP-FPM) ---
echo ""
echo "--- Step 4: Web server ---"

APACHE_INSTALLED=0
if dpkg -l apache2 2>/dev/null | grep -q "^ii"; then
	APACHE_INSTALLED=1
fi

CADDY_INSTALLED=0
if dpkg -l caddy 2>/dev/null | grep -q "^ii"; then
	CADDY_INSTALLED=1
fi

PHP_FPM_INSTALLED=0
if systemctl list-unit-files php*-fpm.service 2>/dev/null | grep -q "enabled"; then
	PHP_FPM_INSTALLED=1
fi

if [[ "$CADDY_INSTALLED" == "0" ]]; then
	echo "Installing Caddy + PHP-FPM..."
	sudo apt-get -q -y install caddy php-fpm php php-gd php-curl php-xml php-json

	if [[ "$APACHE_INSTALLED" == "1" ]]; then
		echo "Stopping and disabling Apache..."
		sudo systemctl stop apache2 2>/dev/null || true
		sudo systemctl disable apache2 2>/dev/null || true
	fi

	echo "Adding caddy to ssl-cert group..."
	sudo usermod -aG ssl-cert caddy 2>/dev/null

	echo "Caddy + PHP-FPM installed."
else
	echo "Caddy already installed."
fi

if [[ "$PHP_FPM_INSTALLED" == "0" ]]; then
	echo "Enabling PHP-FPM..."
	sudo systemctl enable php*-fpm 2>/dev/null
	sudo systemctl start php*-fpm 2>/dev/null
fi

# Ensure webroot is readable
sudo chmod -R a+rX /var/www/html 2>/dev/null

# --- Step 5: Install remaining required packages ---
echo ""
echo "--- Step 5: Additional packages ---"

REQUIRED_PACKAGES="vim bc jq curl socat sshpass sudo ssl-cert inotify-tools iptables git mosquitto mosquitto-clients chrony gcc usbutils"

MISSING_PACKAGES=""
for pkg in $REQUIRED_PACKAGES; do
	if ! dpkg -l "$pkg" 2>/dev/null | grep -q "^ii"; then
		MISSING_PACKAGES="$MISSING_PACKAGES $pkg"
	fi
done

if [ -n "$MISSING_PACKAGES" ]; then
	echo "Installing missing packages:$MISSING_PACKAGES"
	sudo apt-get -q -y install $MISSING_PACKAGES
else
	echo "All required packages already installed."
fi

# Install linux-headers for evdev build (if not present)
if ! dpkg -l "linux-headers-$(uname -r)" 2>/dev/null | grep -q "^ii"; then
	sudo apt-get -q -y install "linux-headers-$(uname -r)" 2>/dev/null || true
fi

# --- Step 6: Chrony NTP ---
echo ""
echo "--- Step 6: NTP (Chrony) ---"
if ! systemctl is-active --quiet chrony 2>/dev/null; then
	echo "Configuring chrony..."
	sudo systemctl stop systemd-timesyncd 2>/dev/null || true
	sudo systemctl disable systemd-timesyncd 2>/dev/null || true
	if [ -f "${OPENWBBASEDIR}/data/config/chrony/chrony.conf" ]; then
		sudo cp "${OPENWBBASEDIR}/data/config/chrony/chrony.conf" /etc/chrony/chrony.conf
	fi
	sudo systemctl enable chrony
	sudo systemctl restart chrony
	echo "Chrony configured."
else
	echo "Chrony already active."
fi

# --- Step 7: MOTD ---
echo ""
echo "--- Step 7: MOTD ---"
if [ -f "${OPENWBBASEDIR}/data/config/profile.d/99-openwb-motd.sh" ]; then
	sudo cp "${OPENWBBASEDIR}/data/config/profile.d/99-openwb-motd.sh" /etc/profile.d/99-openwb-motd.sh
	sudo chmod 755 /etc/profile.d/99-openwb-motd.sh
	echo "MOTD installed."
else
	echo "MOTD file not found, skipping."
fi

# --- Step 8: Update sudoers ---
echo ""
echo "--- Step 8: Sudoers ---"
if [ -f "${OPENWBBASEDIR}/data/config/sudoers/caddy" ]; then
	sudo cp "${OPENWBBASEDIR}/data/config/sudoers/caddy" "/etc/sudoers.d/caddy"
	sudo chmod 440 /etc/sudoers.d/caddy
	echo "Caddy sudoers installed."
fi
# Remove old apache sudoers if present
if [ -f "/etc/sudoers.d/apache2" ]; then
	echo "Removing old Apache sudoers..."
	sudo rm -f "/etc/sudoers.d/apache2"
fi

# --- Step 9: Update service files ---
echo ""
echo "--- Step 9: Service files ---"
for svc in openwb2 openwb-simpleAPI openwbRemoteSupport; do
	svc_file="${OPENWBBASEDIR}/data/config/${svc}.service"
	svc_target="/etc/systemd/system/${svc}.service"
	if [ -f "$svc_file" ]; then
		if [ -L "$svc_target" ]; then
			echo "  ${svc}.service already a symlink, OK."
		else
			sudo rm -f "$svc_target"
			sudo ln -s "$svc_file" "$svc_target"
			echo "  ${svc}.service symlinked."
		fi
	fi
done
sudo systemctl daemon-reload

# --- Step 10: Remove obsolete Apache packages (after everything else is set up) ---
echo ""
echo "--- Step 10: Cleanup ---"
if [[ "$APACHE_INSTALLED" == "1" ]] && [[ "$CADDY_INSTALLED" == "1" ]]; then
	echo "Removing Apache packages (Caddy is active)..."
	sudo apt-get -q -y purge libapache2-mod-php apache2 2>/dev/null
	sudo apt-get -q -y autoremove 2>/dev/null
	echo "Apache removed."
else
	echo "No Apache cleanup needed."
fi

# --- Step 11: Install Python requirements ---
echo ""
echo "--- Step 11: Python requirements ---"
if [ -f "${OPENWBBASEDIR}/requirements.txt" ]; then
	echo "Installing Python packages into venv..."
	if $VENV_PATH/bin/python3 -m pip install --only-binary :all: -r "${OPENWBBASEDIR}/requirements.txt" 2>/dev/null; then
		echo "Python packages installed (binary only)."
	else
		echo "Binary install failed, trying with build..."
		$VENV_PATH/bin/python3 -m pip install -r "${OPENWBBASEDIR}/requirements.txt" 2>/dev/null
		echo "Done (with build)."
	fi
else
	echo "requirements.txt not found, skipping."
fi

# --- Step 12: Run Caddy setup ---
echo ""
echo "--- Step 12: Caddy configuration ---"
if [ -f "${OPENWBBASEDIR}/runs/setup_caddy.sh" ]; then
	bash "${OPENWBBASEDIR}/runs/setup_caddy.sh"
else
	echo "setup_caddy.sh not found, skipping."
fi

# --- Step 13: Swap (zram on RPi, swapfile on x86) ---
echo ""
echo "--- Step 13: Swap setup ---"
HAS_SWAP=$(wc -l < /proc/swaps 2>/dev/null)
if [[ "$HAS_SWAP" -le 1 ]]; then
	if [[ "$PLATFORM_IS_RPI" == "true" ]]; then
		echo "Raspberry Pi detected: setting up zram swap..."
		if ! dpkg -l zram-tools 2>/dev/null | grep -q "^ii"; then
			sudo apt-get -q -y install zram-tools
		fi
		if [ ! -f /etc/default/zramswap ] || ! grep -q "^PERCENTAGE=" /etc/default/zramswap 2>/dev/null; then
			echo "PERCENTAGE=50" | sudo tee /etc/default/zramswap > /dev/null
			echo "PRIORITY=100" | sudo tee -a /etc/default/zramswap > /dev/null
			echo "ALGO=lz4" | sudo tee -a /etc/default/zramswap > /dev/null
		fi
		sudo systemctl enable zramswap 2>/dev/null
		sudo systemctl start zramswap 2>/dev/null || sudo systemctl restart zramswap 2>/dev/null
		echo "zram swap configured (50% of RAM, lz4, priority 100)."
	else
		echo "Non-RPi system: setting up swapfile..."
		if [ ! -f /swapfile ]; then
			sudo fallocate -l 512M /swapfile
			sudo chmod 600 /swapfile
			sudo mkswap /swapfile
			sudo swapon /swapfile
			if ! grep -q "^/swapfile" /etc/fstab; then
				echo "/swapfile none swap sw 0 0" | sudo tee -a /etc/fstab > /dev/null
			fi
			echo "512M swapfile created and activated."
		else
			echo "Swapfile already exists."
		fi
	fi
else
	echo "Swap already active ($(wc -l < /proc/swaps) devices)."
fi

# --- Step 14: Raspberry Pi SD card protection ---
echo ""
echo "--- Step 14: SD card protection (RPi only) ---"
if [[ "$PLATFORM_IS_RPI" == "true" ]]; then
	FSTAB_MODIFIED=0

	if ! grep -q "tmpfs.*/var/log" /etc/fstab 2>/dev/null; then
		echo "Adding tmpfs for /var/log..."
		echo "tmpfs /var/log tmpfs defaults,nosuid,nodev,noatime,size=64M 0 0" | sudo tee -a /etc/fstab > /dev/null
		sudo mount /var/log 2>/dev/null || true
		FSTAB_MODIFIED=1
	else
		echo "tmpfs /var/log already in fstab."
	fi

	if ! grep -q "noatime.* / " /etc/fstab 2>/dev/null; then
		if grep -q "^/dev/.* / " /etc/fstab 2>/dev/null; then
			echo "Adding noatime to root partition..."
			sudo sed -i '/^\/dev\/.* \/ / s/defaults/defaults,noatime/' /etc/fstab
			FSTAB_MODIFIED=1
		fi
	else
		echo "noatime already set on root partition."
	fi

	if [ -f /etc/systemd/journald.conf ]; then
		if ! grep -q "^Storage=volatile" /etc/systemd/journald.conf 2>/dev/null; then
			echo "Setting journald to volatile storage..."
			sudo sed -i 's/^#*Storage=.*/Storage=volatile/' /etc/systemd/journald.conf
			sudo systemctl restart systemd-journald 2>/dev/null
		else
			echo "journald already volatile."
		fi
	fi

	if [[ "$FSTAB_MODIFIED" == "1" ]]; then
		echo "Root partition noatime will take effect on next boot."
	fi
else
	echo "Not a Raspberry Pi, skipping SD card protection."
fi

# --- Mark upgrade complete ---
echo "$CURRENT_STACK" > "$UPGRADE_MARKER"
echo ""
echo "=== Stack upgrade to version $CURRENT_STACK complete ==="
echo "  Python: $($VENV_PATH/bin/python3 --version 2>/dev/null)"
echo "  Venv: $VENV_PATH"
echo "  Web: $(dpkg -l caddy 2>/dev/null | grep '^ii' | awk '{print $3}')"
echo "  PHP-FPM: $(systemctl is-active php*-fpm 2>/dev/null || echo unknown)"
echo "  Chrony: $(systemctl is-active chrony 2>/dev/null)"
if [[ "$PLATFORM_IS_RPI" == "true" ]]; then
	echo "  Swap: zram ($(swapon --show=SIZE --noheadings 2>/dev/null || echo N/A))"
	echo "  SD protection: active"
else
	SWAP_SIZE=$(swapon --show=SIZE --noheadings 2>/dev/null | head -1)
	echo "  Swap: ${SWAP_SIZE:-none}"
fi
echo "==============================================="
