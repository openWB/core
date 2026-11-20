#!/bin/bash

# X-Display setzen, falls das Skript per SSH ausgeführt wird
export DISPLAY="${DISPLAY:-:0}"

# Parameter übernehmen (Standard: 0)
ORIENTATION="${1}"

if [ -z "$ORIENTATION" ]; then
	if rotation=$(mosquitto_sub -p 1886 -t "openWB/optional/int_display/rotation" -C 1 -W 1); then
		ORIENTATION=$(((rotation / 90 + 4) % 4)) # this allows negative rotation angles
	else
		echo "Keine Ausrichtung angegeben, setze Ausrichtung zurück"
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
		echo "Ungültige Ausrichtung: $ORIENTATION (Erlaubt: 0, 1, 2, 3)" >&2
		exit 1
		;;
esac

# Ersten verbundenen Display-Ausgang automatisch ermitteln
OUTPUT=$(xrandr | grep " connected" | awk '{print $1}' | head -n 1)

if [ -n "$OUTPUT" ]; then
	echo "Drehe Display: $OUTPUT"
	xrandr --output "$OUTPUT" --rotate "$ROTATE"
else
	echo "Kein verbundenes Display gefunden." >&2
	exit 1
fi

# Touchscreen-ID automatisch über bekannte Suchmuster ermitteln (ignoriert Groß-/Kleinschreibung)
TOUCH_ID=$(xinput list | grep -iE "ft5x06|touch|goodix|ilitek|egalax" | grep "slave  pointer" | grep -oE "id=[0-9]+" | head -n 1 | cut -d'=' -f2)

# xinput nur aufrufen, wenn eine ID gefunden wurde
if [ -n "$TOUCH_ID" ]; then
	echo "Toucheingabe: $TOUCH_ID"
	xinput set-prop "$TOUCH_ID" "Coordinate Transformation Matrix" $MATRIX
else
	echo "keine Toucheingabe gefunden"
fi
