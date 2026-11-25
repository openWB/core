#!/bin/bash
# Install the precompiled alpha display on the supported Trixie arm64 DSI profile.
set -euo pipefail
SUPPORTED_ARCH=("arm64")
PACKAGE_VERSION='0.1.0~alpha7.20261125'
DEB_PACKAGE_NAME="openwb-native-display"
PACKAGE_BASE_NAME="${DEB_PACKAGE_NAME}_${PACKAGE_VERSION}"
PACKAGE_BASE_URL="https://openwb.de/uploads/display"
PACKAGE_SHA256='5fbca413ee71f6e97e3606e5f888e97f27765603110a47c87dffc2e35f7836a5'

unsupported() {
	echo "$1"
	exit 0
}

if (( EUID != 0 )); then
	echo 'Run the display installer as root.' >&2
	exit 1
fi

# Load OS release information and determine architecture.
. /etc/os-release
OS_CODENAME="${VERSION_CODENAME:-}"
OS_ARCH=$(dpkg --print-architecture)
if [[ ${OS_CODENAME} != trixie || ! " ${SUPPORTED_ARCH[*]} " =~ ${OS_ARCH} ]]; then
	unsupported "Native alpha display: no package selected for this OS/architecture: ${OS_CODENAME} / ${OS_ARCH}"
fi
DEB_FILE_NAME="${PACKAGE_BASE_NAME}_${OS_ARCH}.deb"
PACKAGE_URL="${PACKAGE_BASE_URL}/${DEB_FILE_NAME}"

# Install the native display package if it is not already installed with the correct version.
if [[ $(dpkg-query -W -f='${db:Status-Status} ${Version}' "${DEB_PACKAGE_NAME}" 2>/dev/null || true) != "installed ${PACKAGE_VERSION}" ]]; then
	APT_CACHE_DIR="/var/cache/apt/archives"
	package_file="${APT_CACHE_DIR}/${DEB_FILE_NAME}"
	partial_file="${APT_CACHE_DIR}/partial/${DEB_FILE_NAME}"

	cleanup() {
		rm -f -- "${partial_file}" "${package_file}"
	}

	trap cleanup EXIT
	install -d /var/cache/apt/archives/partial
	if [[ ! -f ${package_file} ]]; then
		echo "download package from '${PACKAGE_URL}' into '${partial_file}'"
		curl --fail --location --proto '=https' --proto-redir '=https' \
			--connect-timeout 15 --max-time 300 --retry 2 \
			--output "${partial_file}" "${PACKAGE_URL}"
		echo "Prüfsumme: $(sha256sum "${partial_file}")"
		echo "verifying sha256 checksum for '${partial_file}'"
		printf '%s  %s\n' "${PACKAGE_SHA256}" "${partial_file}" | sha256sum --check
		echo "moving '${partial_file}' to '${package_file}'"
		mv "${partial_file}" "${package_file}"
	fi
	echo "verifying sha256 checksum for '${package_file}'"
	printf '%s  %s\n' "${PACKAGE_SHA256}" "${package_file}" | sha256sum --check
	echo "verifying package fields for '${package_file}'"
	test "$(dpkg-deb --field "${package_file}" Package)" = "${DEB_PACKAGE_NAME}"
	test "$(dpkg-deb --field "${package_file}" Architecture)" = "${OS_ARCH}"
	test "$(dpkg-deb --field "${package_file}" Version)" = "${PACKAGE_VERSION}"

	echo "installing package '${package_file}'"
	DEBIAN_FRONTEND=noninteractive apt-get -q -y --no-remove install --no-install-recommends "${package_file}"
fi

# # Refresh owned helpers even when the application package is unchanged.
# install -d /usr/local/lib/openwb-native-display /usr/local/lib/openwb-display-power
# install -m 644 "$PROFILE_DIR/native_display_settings.py" /usr/local/lib/openwb-native-display/native_display_settings.py
# if ! cmp -s "$PROFILE_DIR/display_power_service.py" /usr/local/lib/openwb-display-power/display_power_service.py ||
#    ! cmp -s "$PROFILE_DIR/openwb-display-power.service" /etc/systemd/system/openwb-display-power.service; then
# 	power_changed=true
# 	install -m 644 "$PROFILE_DIR/display_power_service.py" /usr/local/lib/openwb-display-power/display_power_service.py
# 	install -m 644 "$PROFILE_DIR/openwb-display-power.service" /etc/systemd/system/openwb-display-power.service
# fi
# if [[ $existing_profile == false ]]; then
# 	install -d /etc/openwb /etc/openwb-native-display /usr/local/libexec \
# 		/etc/lightdm/lightdm.conf.d /usr/share/xsessions /usr/local/lib/openwb-display-power
# 	install -m 644 "$PROFILE_DIR/openbox.xml" /etc/openwb-native-display/openbox.xml
# 	install -m 755 "$PROFILE_DIR/openwb-native-session" /usr/local/libexec/openwb-native-session
# 	install -m 644 "$PROFILE_DIR/openwb-native.desktop" /usr/share/xsessions/openwb-native.desktop
# 	install -m 644 "$PROFILE_DIR/zz-openwb-native.conf" /etc/lightdm/lightdm.conf.d/zz-openwb-native.conf
# 	install -m 644 "$PROFILE_DIR/display_power_service.py" /usr/local/lib/openwb-display-power/display_power_service.py
# 	install -m 644 "$PROFILE_DIR/openwb-display-power.service" /etc/systemd/system/openwb-display-power.service
# 	sed "s/@USER_UID@/$(id -u openwb)/g" "$PROFILE_DIR/openwb-native-display.service" \
# 		> /etc/systemd/system/openwb-native-display.service
# 	chmod 644 /etc/systemd/system/openwb-native-display.service
# fi

# # Initialize only missing settings, atomically and as their actual owner.
# sudo -u openwb python3 /usr/local/lib/openwb-native-display/native_display_settings.py initialize
# touch /etc/openwb/display-managed-externally
# systemctl daemon-reload
# if [[ $masked_lightdm == true ]]; then
# 	systemctl unmask --runtime lightdm.service
# 	masked_lightdm=false
# fi
# if [[ $install_only == true ]]; then
# 	# Counter enablement by package scripts, including pre-existing LightDM.
# 	systemctl disable lightdm.service openwb-native-display.service openwb-display-power.service
# 	echo 'Native display installed; activation deferred until Core publishes display state.'
# 	exit 0
# fi
# args=(apply --lock-fd 9)
# [[ $existing_profile == false ]] && args+=(--new-session)
# [[ $package_changed == true ]] && args+=(--force)
# [[ $power_changed == true ]] && args+=(--reload-power)
# python3 /usr/local/lib/openwb-native-display/native_display_settings.py "${args[@]}"
