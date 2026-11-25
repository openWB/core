#!/bin/bash

is_raspberry_pi() {
	local model_file=${OPENWB_DEVICE_MODEL:-/proc/device-tree/model}
	[[ -r "$model_file" ]] && grep -q '^Raspberry Pi' "$model_file"
}
