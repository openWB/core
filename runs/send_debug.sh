#!/bin/bash
OPENWBBASEDIR=$(cd `dirname $0`/../../ && pwd)
RAMDISKDIR="${OPENWBBASEDIR}/ramdisk"

sleep 60

debugFile=${RAMDISKDIR}/ramdisk/debug.log
echo $1 > $debugFile
debugemail=$2
echo "############################ system ###############" >> $debugFile
uptime >> $debugFile
free >> $debugFile
echo "############################ storage ###############" >> $debugFile
df -h >> $debugFile
echo "############################ network ##############" >> $debugFile
ifconfig >> $debugFile
echo "############################ version ##############" >> $debugFile
cat ${RAMDISKDIR}/web/version >> $debugFile
cat ${RAMDISKDIR}/web/lastcommit >> $debugFile
echo "############################ main.log ##############" >> $debugFile
echo "$(tail -1000 ${RAMDISKDIR}/ramdisk/main.log)" >> $debugFile
echo "############################ mqtt ##############" >> $debugFile
echo "$(tail -500 ${RAMDISKDIR}/ramdisk/mqtt.log)" >> $debugFile

for currentConfig in /etc/mosquitto/conf.d/99-bridge-*; do
	if [ -f "$currentConfig" ]; then
		echo "############################ mqtt bridge '$currentConfig' ######" >> $debugFile
		sudo grep -F -v -e password "$currentConfig" | sed '/^#/ d'>> $debugFile
	fi
done

echo "############################ mqtt topics ##############" >> $debugFile
timeout 1 mosquitto_sub -v -t 'openWB/#' >> $debugFile

#echo "############################ smarthome.log ##############" >> $debugFile
#echo "$(tail -200 ${RAMDISKDIR}/ramdisk/smarthome.log)" >> $debugFile

curl --upload $debugFile "https://openwb.de/tools/debug2.php?debugemail=$debugemail"

rm $debugFile
