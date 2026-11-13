#!/bin/bash
# Install the precompiled alpha display on the supported Trixie arm64 DSI profile.
set -euo pipefail
OPENWBBASEDIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
PROFILE_DIR="${OPENWBBASEDIR}/data/config/native-display"
PACKAGE_VERSION='0.1.0~alpha3+watermark20261113.1'
PACKAGE_NAME="openwb-native-display_${PACKAGE_VERSION}_arm64.deb"
PACKAGE_URL='https://openwb.de/uploads/display/openwb-native-display_0.1.0~alpha3%2Bwatermark20261113.1_arm64.deb'
PACKAGE_SHA256='fbcfb5d3adb0ef6799e64d9e877d79716ddd9ba681b51141d57ae851b0795f11'

install_only=false
case "$*" in
    '') ;;
    --install-only) install_only=true ;;
    *) echo 'Usage: install_native_display.sh [--install-only]' >&2; exit 2 ;;
esac

unsupported() {
    echo "$1"
    # Let the caller distinguish this run's result from stale installed files.
    if [[ $install_only == true ]]; then exit 10; fi
    exit 0
}

if (( EUID != 0 )); then
    echo 'Run the display installer as root.' >&2
    exit 1
fi
. /etc/os-release
if [[ ${VERSION_CODENAME:-} != trixie || $(dpkg --print-architecture) != arm64 ]]; then
    unsupported 'Native alpha display: no package selected for this OS/architecture.'
fi
display_found=false
for connector in /sys/class/drm/card*-DSI-*; do
    if [[ -f "$connector/status" && $(cat "$connector/status") == connected ]] &&
       grep -qx '800x480' "$connector/modes"; then
        display_found=true
        break
    fi
done
if [[ $display_found != true ]]; then
    unsupported 'Native alpha display: no supported 800x480 DSI panel detected; skipping.'
fi
id openwb >/dev/null
# Share the updater's lock; read MQTT state only after acquiring it.
exec 9>/run/lock/openwb-native-display.lock
flock -x 9
for file in openbox.xml openwb-native-session openwb-native.desktop zz-openwb-native.conf \
            openwb-native-display.service display_power_service.py openwb-display-power.service \
            native_display_settings.py; do
    test -r "$PROFILE_DIR/$file"
done

existing_profile=false
package_changed=false
power_changed=false
masked_lightdm=false
if [[ -f /etc/systemd/system/openwb-native-display.service ]]; then
    if [[ ! -f /etc/openwb/display-managed-externally ]]; then
        echo 'A separately managed native display service exists; refusing to overwrite it.' >&2
        exit 1
    fi
    existing_profile=true
fi

# Standalone updates preserve the previous unknown-state policy. Initial
# provisioning must also work before Core has published any broker state.
if [[ $install_only == true ]]; then
    :
elif python3 "$PROFILE_DIR/native_display_settings.py" preflight; then
    :
else
    status=$?
    if [[ $status == 75 ]]; then
        echo 'Native display state unavailable; installation deferred without service changes.'
        exit 0
    fi
    exit "$status"
fi

if [[ $install_only == true ]]; then
    # Persistent start conditions also block package-maintainer service starts
    # and survive a reboot during installation. Only valid broker state may
    # release this guard in native_display_settings.py.
    install -d /etc/openwb
    touch /etc/openwb/native-display-activation-pending
    for unit in lightdm.service openwb-native-display.service openwb-display-power.service; do
        dropin="/etc/systemd/system/$unit.d/20-openwb-provisioning.conf"
        contents=$'[Unit]\nConditionPathExists=!/etc/openwb/native-display-activation-pending'
        if [[ -e $dropin && $(cat "$dropin") != "$contents" ]]; then
            echo "Refusing to overwrite unrelated provisioning guard: $dropin" >&2
            exit 1
        fi
        install -d "/etc/systemd/system/$unit.d"
        printf '%s\n' "$contents" > "$dropin"
    done
    systemctl daemon-reload
    for unit in openwb-native-display.service lightdm.service openwb-display-power.service; do
        if [[ $(systemctl show "$unit" --property=LoadState --value) == loaded ]]; then
            systemctl stop "$unit"
            systemctl disable "$unit"
        fi
    done
fi

if [[ $(dpkg-query -W -f='${db:Status-Status} ${Version}' openwb-native-display 2>/dev/null || true) != "installed $PACKAGE_VERSION" ]]; then
package_file="/var/cache/apt/archives/$PACKAGE_NAME"
partial_file="/var/cache/apt/archives/partial/$PACKAGE_NAME"
cleanup() {
    rm -f -- "$partial_file" "$package_file"
    if [[ $masked_lightdm == true ]]; then
        systemctl unmask --runtime lightdm.service >/dev/null
    fi
}
trap cleanup EXIT
install -d /var/cache/apt/archives/partial
if [[ ! -f $package_file ]]; then
    curl --fail --location --proto '=https' --proto-redir '=https' \
        --connect-timeout 15 --max-time 300 --retry 2 \
        --output "$partial_file" "$PACKAGE_URL"
    printf '%s  %s\n' "$PACKAGE_SHA256" "$partial_file" | sha256sum --check --status
    mv "$partial_file" "$package_file"
fi
printf '%s  %s\n' "$PACKAGE_SHA256" "$package_file" | sha256sum --check --status
test "$(dpkg-deb --field "$package_file" Package)" = openwb-native-display
test "$(dpkg-deb --field "$package_file" Architecture)" = arm64
test "$(dpkg-deb --field "$package_file" Version)" = "$PACKAGE_VERSION"

# A new LightDM must not start before its native-only session exists.
if [[ $install_only != true ]] && ! dpkg-query -W -f='${db:Status-Status}' lightdm 2>/dev/null | grep -qx installed; then
    if [[ ! -e /run/systemd/system/lightdm.service && ! -L /run/systemd/system/lightdm.service &&
          ! -L /etc/systemd/system/lightdm.service ]]; then
        systemctl mask --runtime lightdm.service
        masked_lightdm=true
    fi
fi
if [[ ${OPENWB_APT_INDEX_READY:-0} != 1 ]]; then
    apt-get -q -o APT::Update::Error-Mode=any update
fi
DEBIAN_FRONTEND=noninteractive apt-get -q -y --no-remove install --no-install-recommends \
    "$package_file" xserver-xorg-core xserver-xorg-input-libinput xauth \
    x11-xserver-utils x11-utils lightdm openbox python3

package_changed=true
fi

# Refresh owned helpers even when the application package is unchanged.
install -d /usr/local/lib/openwb-native-display /usr/local/lib/openwb-display-power
install -m 644 "$PROFILE_DIR/native_display_settings.py" /usr/local/lib/openwb-native-display/native_display_settings.py
if ! cmp -s "$PROFILE_DIR/display_power_service.py" /usr/local/lib/openwb-display-power/display_power_service.py ||
   ! cmp -s "$PROFILE_DIR/openwb-display-power.service" /etc/systemd/system/openwb-display-power.service; then
    power_changed=true
    install -m 644 "$PROFILE_DIR/display_power_service.py" /usr/local/lib/openwb-display-power/display_power_service.py
    install -m 644 "$PROFILE_DIR/openwb-display-power.service" /etc/systemd/system/openwb-display-power.service
fi
if [[ $existing_profile == false ]]; then
install -d /etc/openwb /etc/openwb-native-display /usr/local/libexec \
    /etc/lightdm/lightdm.conf.d /usr/share/xsessions /usr/local/lib/openwb-display-power
install -m 644 "$PROFILE_DIR/openbox.xml" /etc/openwb-native-display/openbox.xml
install -m 755 "$PROFILE_DIR/openwb-native-session" /usr/local/libexec/openwb-native-session
install -m 644 "$PROFILE_DIR/openwb-native.desktop" /usr/share/xsessions/openwb-native.desktop
install -m 644 "$PROFILE_DIR/zz-openwb-native.conf" /etc/lightdm/lightdm.conf.d/zz-openwb-native.conf
install -m 644 "$PROFILE_DIR/display_power_service.py" /usr/local/lib/openwb-display-power/display_power_service.py
install -m 644 "$PROFILE_DIR/openwb-display-power.service" /etc/systemd/system/openwb-display-power.service
sed "s/@USER_UID@/$(id -u openwb)/g" "$PROFILE_DIR/openwb-native-display.service" \
    > /etc/systemd/system/openwb-native-display.service
chmod 644 /etc/systemd/system/openwb-native-display.service

fi
# Initialize only missing settings, atomically and as their actual owner.
sudo -u openwb python3 /usr/local/lib/openwb-native-display/native_display_settings.py initialize
touch /etc/openwb/display-managed-externally
systemctl daemon-reload
if [[ $masked_lightdm == true ]]; then
    systemctl unmask --runtime lightdm.service
    masked_lightdm=false
fi
if [[ $install_only == true ]]; then
    # Counter enablement by package scripts, including pre-existing LightDM.
    systemctl disable lightdm.service openwb-native-display.service openwb-display-power.service
    echo 'Native display installed; activation deferred until Core publishes display state.'
    exit 0
fi
args=(apply --lock-fd 9)
[[ $existing_profile == false ]] && args+=(--new-session)
[[ $package_changed == true ]] && args+=(--force)
[[ $power_changed == true ]] && args+=(--reload-power)
python3 /usr/local/lib/openwb-native-display/native_display_settings.py "${args[@]}"
