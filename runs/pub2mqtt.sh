#!/bin/bash

declare -A mqttvar
mqttvar["chargepoint/get/counter_all"]=llkwhges
mqttvar["chargepoint/get/power_all"]=llkombiniert
mqttvar["chargepoint/1/get/counter"]=llkwh
mqttvar["chargepoint/1/get/charge_state"]=chargestat
mqttvar["chargepoint/1/get/plug_state"]=plugstat
mqttvar["chargepoint/1/get/phases_in_use"]=lp1phasen
mqttvar["chargepoint/1/get/charged_since_plugged_counter"]=aktgeladen
mqttvar["chargepoint/2/get/counter"]=llkwhs1
mqttvar["chargepoint/2/get/charge_state"]=chargestats1
mqttvar["chargepoint/2/get/plug_state"]=plugstats1
mqttvar["chargepoint/2/get/phases_in_use"]=lp2phasen
mqttvar["chargepoint/2/get/charged_since_plugged_counter"]=aktgeladens1
mqttvar["chargepoint/3/get/counter"]=llkwhs2
mqttvar["chargepoint/3/get/charge_state"]=chargestats2
mqttvar["chargepoint/3/get/plug_state"]=plugstats2
mqttvar["chargepoint/3/get/phases_in_use"]=lp3phasen
mqttvar["chargepoint/3/get/charged_since_plugged_counter"]=aktgeladens2
mqttvar["pv/1/get/counter"]=pvkwh
mqttvar["pv/1/get/power"]=pv1watt
mqttvar["pv/1/get/daily_yield"]=daily_pvkwhk1
mqttvar["pv/1/get/monthly_yield"]=monthly_pvkwhk1
mqttvar["pv/1/get/yearly_yield"]=yearly_pvkwhk1
mqttvar["pv/2/get/counter"]=pv2kwh
mqttvar["pv/2/get/power"]=pv2watt
mqttvar["pv/2/get/daily_yield"]=daily_pvkwhk2
mqttvar["pv/2/get/monthly_yield"]=monthly_pvkwhk2
mqttvar["pv/2/get/yearly_yield"]=yearly_pvkwhk2
mqttvar["bat/1/get/soc"]=speichersoc
mqttvar["bat/1/get/power"]=speicherleistung
mqttvar["bat/1/get/imported"]=speicherikwh
mqttvar["bat/1/get/exported"]=speicherekwh
mqttvar["bat/1/get/daily_yield_export"]=daily_sekwh
mqttvar["bat/1/get/daily_yield_import"]=daily_sikwh
mqttvar["counter/0/get/power_all"]=wattbezug
mqttvar["counter/0/get/current"]=evua1
mqttvar["counter/0/get/voltage"]=evuv1
mqttvar["counter/0/get/imported"]=bezugkwh
mqttvar["counter/0/get/exported"]=einspeisungkwh
mqttvar["vehicle/1/get/soc"]=soc
mqttvar["counter/set/home_consumption"]=hausverbrauch
numOfChargepoints=$(</var/www/html/openWB/ramdisk/ConfiguredChargePoints)
for i in $(seq 1 $numOfChargepoints);
do
	for f in \
		"chargepoint/${i}/get/power_all:ladeleistunglp${i}" \
		"chargepoint/${i}/get/phases_in_use:lp${i}phasen" 
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

sleep 0.5
mosquitto_pub -r -t openWB/set/loadvarsdone -m 1