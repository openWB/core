#!/bin/bash

evua1=$(curl -s 192.168.40.248/openWB/ramdisk/bezuga1)
evua2=$(curl -s 192.168.40.248/openWB/ramdisk/bezuga2)
evua3=$(curl -s 192.168.40.248/openWB/ramdisk/bezuga3)
echo -n $evua1 > /var/www/html/openWB/ramdisk/bezuga1
echo -n $evua2 > /var/www/html/openWB/ramdisk/bezuga2
echo -n $evua3 > /var/www/html/openWB/ramdisk/bezuga3
mosquitto_pub -r -t "openWB/set/counter/0/get/current" -m "[$evua1,$evua2,$evua3]"
soc=$(curl -s 192.168.40.248/openWB/ramdisk/soc)
#soc=91
mosquitto_pub -r -t "openWB/set/vehicle/1/get/soc" -m "$soc"
pvwatt=$(curl -s 192.168.40.248/openWB/ramdisk/pvwatt)
mosquitto_pub -r -t "openWB/set/pv/1/get/counter" -m "$pvwatt"
bezugwatt=$(curl -s 192.168.40.248/openWB/ramdisk/wattbezug)
mosquitto_pub -r -t "openWB/set/counter/0/get/power_all" -m "$bezugwatt"

current=$(timeout 1 mosquitto_sub -t 'openWB/chargepoint/1/set/current')
#echo $current > /var/www/html/openWB/ramdisk/actcurrlp1
mosquitto_pub -r -t "openWB/set/isss/Current" -h 192.168.1.221 -m "$current"
ll=$(timeout 1 mosquitto_sub -C 1 -h 192.168.1.221 -t 'openWB/lp/1/W')
mosquitto_pub -r -t "openWB/set/chargepoint/1/get/power_all" -m "$ll"
plug=$(timeout 1 mosquitto_sub -C 1 -h 192.168.1.221 -t 'openWB/lp/1/boolPlugStat')
mosquitto_pub -r -t "openWB/set/chargepoint/1/get/plug_state" -m "$plug"
charge=$(timeout 1 mosquitto_sub -C 1 -h 192.168.1.221 -t 'openWB/lp/1/boolChargeStat')
mosquitto_pub -r -t "openWB/set/chargepoint/1/get/charge_state" -m "$charge"
current_p1=$(timeout 1 mosquitto_sub -C 1 -h 192.168.1.221 -t 'openWB/lp/1/APhase1')
current_p2=$(timeout 1 mosquitto_sub -C 1 -h 192.168.1.221 -t 'openWB/lp/1/APhase2')
current_p3=$(timeout 1 mosquitto_sub -C 1 -h 192.168.1.221 -t 'openWB/lp/1/APhase3')
mosquitto_pub -r -t "openWB/set/chargepoint/1/get/current" -m "[$current_p1,$current_p2,$current_p3]"
phases_in_use=$(timeout 1 mosquitto_sub -C 1 -h 192.168.1.221 -t 'openWB/lp/1/countPhasesInUse')
mosquitto_pub -r -t "openWB/set/chargepoint/1/get/phases_in_use" -m "$phases_in_use"




