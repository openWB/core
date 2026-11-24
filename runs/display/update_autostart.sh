#!/bin/bash
OPENWB_BASE_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
LOGFILE="${OPENWB_BASE_DIR}/ramdisk/update_local_display.log"

# set "forceUpdate" to parameter $1, set to 0 if not set
forceUpdate=${1:-0}

versionMatch() {
	file=$1
	target=$2
	currentVersion=$(grep -o "openwb-version:[0-9]\+" "$file" | grep -o "[0-9]\+$")
	installedVersion=$(sudo grep -o "openwb-version:[0-9]\+" "$target" | grep -o "[0-9]\+$")
	if ((currentVersion == installedVersion)); then
		return 0
	else
		return 1
	fi
}

{
	restartRequired=0
	echo "### Updating display autostart settings ###"
	if displayTheme=$(mosquitto_sub -p 1886 -t "openWB/optional/int_display/theme" -C 1 -W 1); then
		echo "display theme: $displayTheme"
		displayThemeType=$(jq -r '.type' <<< "$displayTheme")
		# check if file "runtime" exists in theme runtime directory
		echo "display theme type: $displayThemeType"
		echo "runtime file: ${OPENWB_BASE_DIR}/packages/modules/display_themes/$displayThemeType/runtime"
		if [[ -e "${OPENWB_BASE_DIR}/packages/modules/display_themes/$displayThemeType/runtime" ]]; then
			echo "runtime file exists in theme directory"
			if versionMatch "${OPENWB_BASE_DIR}/data/config/display/lxdeautostart.runtime" "/home/openwb/.config/lxsession/LXDE/autostart"; then
				echo "lxde session autostart already configured"
			else
				echo "updating lxde session autostart"
				cp "${OPENWB_BASE_DIR}/data/config/display/lxdeautostart.runtime" "/home/openwb/.config/lxsession/LXDE/autostart"
				# replace pattern "#RUNTIME#" with the actual runtime file path
				sed -i "s|#RUNTIME#|${OPENWB_BASE_DIR}/packages/modules/display_themes/$displayThemeType/runtime|g" "/home/openwb/.config/lxsession/LXDE/autostart"
				restartRequired=1
			fi
		else
			echo "runtime file missing in theme directory, using browser based display"
			if versionMatch "${OPENWB_BASE_DIR}/data/config/display/lxdeautostart.browser" "/home/openwb/.config/lxsession/LXDE/autostart"; then
				echo "lxde session autostart already configured"
			else
				echo "updating lxde session autostart"
				cp "${OPENWB_BASE_DIR}/data/config/display/lxdeautostart.browser" "/home/openwb/.config/lxsession/LXDE/autostart"
				restartRequired=1
			fi
		fi
	fi
	if ((restartRequired == 1)) || ((forceUpdate == 1)); then
		echo "Restarting display manager due to autostart changes"
		sudo systemctl restart lightdm.service
	fi
} >> "$LOGFILE" 2>&1
