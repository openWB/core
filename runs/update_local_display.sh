#!/bin/bash
OPENWB_BASE_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
# set "forceUpdate" to parameter $1, set to 0 if not set
forceUpdate=${1:-0}
LOGFILE="${OPENWB_BASE_DIR}/ramdisk/update_local_display.log"

# set X-Display if the script is executed via SSH or TTY
export DISPLAY="${DISPLAY:-:0}"

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

# # Native profiles consume local broker rotation, standby and PIN settings.
# # Do not edit LXDE/firmware settings or restart a healthy native X11 session.
# if [[ -f /etc/openwb/display-managed-externally ]]; then
# 	args=()
# 	[[ "$forceUpdate" == 1 ]] && args+=(--force)
# 	exec sudo python3 /usr/local/lib/openwb-native-display/native_display_settings.py apply "${args[@]}"
# fi

{
	# check autostart
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
				displaySetupModified=1
			fi
		else
			echo "runtime file missing in theme directory, using browser based display"
			if versionMatch "${OPENWB_BASE_DIR}/data/config/display/lxdeautostart.browser" "/home/openwb/.config/lxsession/LXDE/autostart"; then
				echo "lxde session autostart already configured"
			else
				echo "updating lxde session autostart"
				cp "${OPENWB_BASE_DIR}/data/config/display/lxdeautostart.browser" "/home/openwb/.config/lxsession/LXDE/autostart"
				displaySetupModified=1
			fi
		fi
		if ((displaySetupModified == 1)) || ((forceUpdate == 1)); then
			# update display standby timeout
			if timeout=$(mosquitto_sub -p 1886 -t "openWB/optional/int_display/standby" -C 1 -W 1); then
				echo "new display timeout value: '$timeout'"
			else
				echo "failed getting configured display timeout value!"
				echo "setting default value of 60s"
				timeout=60
			fi
			sudo sed -i '/^xset -dpms/d' "/home/openwb/.config/lxsession/LXDE/autostart"
			if [[ "$timeout" == 0 ]]; then
				# disable display standby and DPMS
				sed -i "s/^xset s .*$/xset s off\nxset -dpms/" "/home/openwb/.config/lxsession/LXDE/autostart"
				# apply display standby settings immediately
				xset s off
				xset -dpms
			else
				# set display standby timeout and enable DPMS
				sed -i "s/^xset s .*$/xset s ${timeout}/" "/home/openwb/.config/lxsession/LXDE/autostart"
				# apply display standby settings immediately
				xset s "$timeout"
				xset +dpms
			fi

			# update display rotation
			"${OPENWB_BASE_DIR}/runs/rotate_display.sh"

			# enable/disable display
			default_target=$(systemctl get-default)
			if display_active=$(mosquitto_sub -p 1886 -t "openWB/optional/int_display/active" -C 1 -W 1) && [[ $display_active == "true" ]] && display_detected=$(mosquitto_sub -p 1886 -t "openWB/optional/int_display/detected" -C 1 -W 1) && [[ $display_detected == "true" ]]; then
				if [[ $default_target == "graphical.target" ]]; then
					echo "graphical target already configured"
				else
					echo "setting graphical target as default"
					sudo systemctl set-default graphical.target
				fi
				# only restart display manager if boot done or forceUpdate is set
				if [[ -f "${OPENWB_BASE_DIR}/ramdisk/bootdone" ]] || ((forceUpdate == 1)); then
					echo "restarting lightdm service"
					sudo systemctl restart lightdm.service
				fi
			else
				if [[ $default_target == "multi-user.target" ]]; then
					echo "multi-user target already configured"
				else
					echo "setting multi-user target as default"
					sudo systemctl set-default multi-user.target
				fi
				echo "internal display not activated, stopping lightdm service if running"
				sudo systemctl stop lightdm.service
			fi
		fi
	fi
} >> "$LOGFILE" 2>&1
