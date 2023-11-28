#!/bin/bash
OPENWBBASEDIR=$(cd "$(dirname "$0")/../" && pwd)
RAMDISKDIR="${OPENWBBASEDIR}/ramdisk"


function merge_log_files(){
	LOGPATH=${3:-$RAMDISKDIR}
	if [[ -f "${LOGPATH}/${1}.log.1" ]]; then
		cat "${LOGPATH}/${1}.log.1" "${LOGPATH}/${1}.log" | tail -n $2
	else
		tail -n $2 "${LOGPATH}/${1}.log"
	fi
}

debugFile="${RAMDISKDIR}/debug.log"
touch "$debugFile"
{
	echo "$1" | jq -r .message
	debugEmail=$(echo "$1" | jq -r .email)
	echo "$debugEmail"
	echo "${1}" | jq -r .serialNumber
	echo "${1}" | jq -r .installedComponents
	echo "${1}" | jq -r .vehicles
	echo "############################ version ##############"
	cat "${OPENWBBASEDIR}/web/version"
	cat "${OPENWBBASEDIR}/web/lastcommit"
	echo "############################ configuration and state ##############"
	echo "${2}"
	echo "############################ system ###############"
	uptime
	free
	echo "############################ uuids ##############"
	cat "${OPENWBBASEDIR}/data/log/uuid"
	echo "############################ retained log ##############"
	merge_log_files "main" 500
	echo "############################ info log ##############"
	mosquitto_pub -p 1886 -t "openWB/set/system/debug_level" -m "20"
	sleep 60
	merge_log_files "main" 1000
	echo "############################ debug log ##############"
	mosquitto_pub -p 1886 -t "openWB/set/system/debug_level" -m "10"
	sleep 60
	merge_log_files "main" 2500
	echo "############################ internal chargepoint log ##############"
	merge_log_files "internal_chargepoint" 1000
	echo "############################ mqtt log ##############"
	merge_log_files "mqtt" 1000
	echo "############################ soc log ##############"
	merge_log_files "soc" 1000

	for currentConfig in /etc/mosquitto/conf.d/99-bridge-*; do
		if [ -f "$currentConfig" ]; then
			echo "############################ mqtt bridge '$currentConfig' ######"
			sudo grep -F -v -e password "$currentConfig" | sed '/^#/ d'
		fi
	done

	echo "############################ broker ##############"
	timeout 1 mosquitto_sub -v -t 'openWB/#'
	echo "############################ storage ###############"
	df -h
	echo "############################ network ##############"
	ifconfig
	# echo "############################ smarthome.log ##############"
	# merge_log_files "smarthome" 200
} >>"$debugFile"

echo "***** uploading debug log..." >>"$RAMDISKDIR/main.log"
curl --upload "$debugFile" "https://openwb.de/tools/debug2.php?debugemail=$debugEmail"

echo "***** cleanup..." >>"$RAMDISKDIR/main.log"
rm "$debugFile"

echo "***** debug log end" >>"$RAMDISKDIR/main.log"
