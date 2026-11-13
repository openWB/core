#!/bin/bash
# Install the precompiled alpha display on the supported Trixie arm64 DSI profile.
set -euo pipefail
OPENWBBASEDIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
PROFILE_DIR="${OPENWBBASEDIR}/data/config/native-display"
PACKAGE_NAME='openwb-native-display_0.1.0~alpha3+watermark20261113_arm64.deb'
PACKAGE_URL='https://openwb.de/uploads/display/openwb-native-display_0.1.0~alpha3%2Bwatermark20261113_arm64.deb'
PACKAGE_SHA256='7dafd661a873aa29551e3bf7eab8c9479e23401adc81b1e84449e1aff0b430ca'

if (( EUID != 0 )); then
    echo 'Run the display installer as root.' >&2
    exit 1
fi
. /etc/os-release
if [[ ${VERSION_CODENAME:-} != trixie || $(dpkg --print-architecture) != arm64 ]]; then
    echo 'Native alpha display: no package selected for this OS/architecture.'
    exit 0
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
    echo 'Native alpha display: no supported 800x480 DSI panel detected; skipping.'
    exit 0
fi
id openwb >/dev/null
for file in openbox.xml openwb-native-session openwb-native.desktop zz-openwb-native.conf \
            openwb-native-display.service display_power_service.py openwb-display-power.service; do
    test -r "$PROFILE_DIR/$file"
done

if [[ -f /etc/openwb/display-managed-externally &&
      -f /etc/systemd/system/openwb-native-display.service ]] &&
   [[ $(dpkg-query -W -f='${Version}' openwb-native-display 2>/dev/null || true) == '0.1.0~alpha3+watermark20261113' ]]; then
    bash "$OPENWBBASEDIR/runs/update_local_display.sh"
    echo 'Native alpha display is already installed; display settings applied without reinstalling.'
    exit 0
fi

package_file="/var/cache/apt/archives/$PACKAGE_NAME"
partial_file="/var/cache/apt/archives/partial/$PACKAGE_NAME"
masked_lightdm=false
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
test "$(dpkg-deb --field "$package_file" Version)" = '0.1.0~alpha3+watermark20261113'

# A new LightDM must not start before its native-only session exists.
if ! dpkg-query -W -f='${db:Status-Status}' lightdm 2>/dev/null | grep -qx installed; then
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

# Application upgrades preserve an already configured native session and overrides.
if [[ -f /etc/openwb/display-managed-externally &&
      -f /etc/systemd/system/openwb-native-display.service ]]; then
    systemctl try-restart openwb-native-display.service
    echo 'Native alpha display package updated; existing display profile preserved.'
    exit 0
fi
if [[ -f /etc/systemd/system/openwb-native-display.service ]]; then
    echo 'A separately managed native display service exists; refusing to overwrite it.' >&2
    exit 1
fi
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

# Initialize only missing local transport/display settings; never copy another box's settings.
sudo -u openwb python3 - <<'PY'
from pathlib import Path
import subprocess
folder=Path.home()/'native-display'
folder.mkdir(mode=0o700, exist_ok=True)
settings=folder/'display.ini'
if not settings.exists():
    result=subprocess.run(['mosquitto_sub','-h','localhost','-p','1886','-t',
                           'openWB/optional/int_display/rotation','-C','1','-W','2'],
                          capture_output=True,text=True,timeout=4)
    rotation='180' if result.stdout.strip()=='180' else '0'
    settings.write_text('[display]\nrotation='+rotation+'\nstyle=graphic\n\n'
                        '[mqtt]\nlocalPort=1886\nlocalHttpPort=81\n\n'
                        '[presentation]\noverviewPanel=glass-flow\n')
    settings.chmod(0o600)
PY
touch /etc/openwb/display-managed-externally
systemctl daemon-reload
if [[ $masked_lightdm == true ]]; then
    systemctl unmask --runtime lightdm.service
    masked_lightdm=false
fi
systemctl enable lightdm.service openwb-display-power.service openwb-native-display.service
display_active=$(mosquitto_sub -h localhost -p 1886 -t openWB/optional/int_display/active -C 1 -W 2 2>/dev/null || true)
if [[ $display_active == false ]]; then
    echo 'Native alpha display installed; existing disabled-display setting preserved.'
    exit 0
fi
systemctl set-default graphical.target
systemctl start openwb-display-power.service
# A pre-existing graphical session needs exactly one session switch.
systemctl restart lightdm.service
systemctl start openwb-native-display.service
sleep 5
for unit in lightdm.service openwb-display-power.service openwb-native-display.service; do
    systemctl is-active --quiet "$unit"
done
echo 'Native alpha display installed and active.'
