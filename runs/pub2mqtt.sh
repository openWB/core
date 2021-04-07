#!/bin/bash

declare -A mqttvar
mqttvar["chargepoint/get/counter_all"]=llkwhges
mqttvar["chargepoint/get/power_all"]=llkombiniert
mqttvar["chargepoint/1/get/voltage"]=llv1
mqttvar["chargepoint/1/get/current"]=lla1
mqttvar["chargepoint/1/get/counter"]=llkwh
mqttvar["chargepoint/1/get/charge_state"]=chargestat
mqttvar["chargepoint/1/get/plug_state"]=plugstat
mqttvar["chargepoint/1/get/"]=aktgeladen
mqttvar["pv/get/counter"]=pvallwh
mqttvar["pv/get/power"]=pvwatt
mqttvar["bat/get/soc"]=speichersoc
mqttvar["bat/get/power"]=speicherleistung
mqttvar["counter/1/get/power_all"]=wattbezugint
mqttvar["counter/1/get/current"]=evua1
mqttvar["counter/1/get/voltage"]=evuv1
mqttvar["counter/1/get/imported"]=bezugkwh
mqttvar["counter/1/get/exported"]=einspeisungkwh


for i in $(seq 1 8);
do
	for f in \
		"chargepoint/${i}/power_all:ladeleistunglp${i}" \
		"chargepoint/${i}/phases_in_use:lp${i}phasen" 
	do
		IFS=':' read -r -a tuple <<< "$f"
		#echo "Setting mqttvar[${tuple[0]}]=${tuple[1]}"
		mqttvar["${tuple[0]}"]=${tuple[1]}
	done
done



tempPubList=""
for mq in "${!mqttvar[@]}"; do
	declare o${mqttvar[$mq]}
	declare ${mqttvar[$mq]}
	tempnewname=${mqttvar[$mq]}
	tempoldname=o${mqttvar[$mq]}

	if [ -r ramdisk/"${mqttvar[$mq]}" ]; then

		tempnewname=$(<ramdisk/"${mqttvar[$mq]}")

		if [ -r ramdisk/mqtt2"${mqttvar[$mq]}" ]; then
			tempoldname=$(<ramdisk/mqtt2"${mqttvar[$mq]}")
		else
			tempoldname=""
		fi

		if [[ "$tempoldname" != "$tempnewname" ]]; then
			tempPubList="${tempPubList}\nopenWB/${mq}=${tempnewname}"
			echo $tempnewname > ramdisk/mqtt2${mqttvar[$mq]}
		fi
		#echo ${mqttvar[$mq]} $mq
	fi
done


#echo "Publist:"
#echo -e $tempPubList

#echo "Running Python:"
echo -e $tempPubList | python3 runs/mqttpub.py -q 0 -r &
