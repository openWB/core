#!/bin/bash
OPENWB_BASE_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
LOGFILE="${OPENWB_BASE_DIR}/ramdisk/update_local_display.log"

# set X-Display if the script is executed via SSH or TTY
export DISPLAY="${DISPLAY:-:0}"

# take parameter (default: 0)
ORIENTATION="${1}"

{
	echo "### Updating display rotation settings ###"
	if [ -z "$ORIENTATION" ]; then
		if rotation=$(mosquitto_sub -p 1886 -t "openWB/optional/int_display/rotation" -C 1 -W 1); then
			echo "Detected rotation from MQTT: $rotation"
			ORIENTATION=$(((rotation / 90 + 4) % 4)) # this allows negative rotation angles
			echo "Calculated orientation: $ORIENTATION"
		else
			echo "No orientation specified, resetting orientation"
			ORIENTATION=0
		fi
	fi

	case "$ORIENTATION" in
		0)
			ROTATE="normal"
			MATRIX="1 0 0 0 1 0 0 0 1"
			;;
		1)
			ROTATE="right"
			MATRIX="0 1 0 -1 0 1 0 0 1"
			;;
		2)
			ROTATE="inverted"
			MATRIX="-1 0 1 0 -1 1 0 0 1"
			;;
		3)
			ROTATE="left"
			MATRIX="0 -1 1 1 0 0 0 0 1"
			;;
		*)
			echo "Invalid orientation: $ORIENTATION (Allowed: 0, 1, 2, 3)" >&2
			exit 1
			;;
	esac

	# detect first connected display output automatically
	OUTPUT=$(xrandr | grep " connected" | awk '{print $1}' | head -n 1)

	if [ -n "$OUTPUT" ]; then
		echo "Drehe Display: $OUTPUT"
		xrandr --output "$OUTPUT" --rotate "$ROTATE"
	else
		echo "No connected display found." >&2
		exit 1
	fi

	# detect Touchscreen ID automatically using known patterns (case-insensitive)
	TOUCH_ID=$(xinput list | grep -iE "ft5x06|touch|goodix|ilitek|egalax" | grep "slave  pointer" | grep -oE "id=[0-9]+" | head -n 1 | cut -d'=' -f2)

	# only call xinput if an ID was found
	if [ -n "$TOUCH_ID" ]; then
		echo "Touch ID: $TOUCH_ID"
		xinput set-prop "$TOUCH_ID" "Coordinate Transformation Matrix" $MATRIX
	else
		echo "no touch input detected"
	fi
} >> "$LOGFILE" 2>&1
