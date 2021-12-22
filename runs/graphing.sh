#!/bin/bash
OPENWBBASEDIR=$(cd `dirname $0`/../ && pwd)
livegraph=$1
echo "$(tail -$livegraph ${OPENWBBASEDIR}/ramdisk/graph_live.json)" > ${OPENWBBASEDIR}/ramdisk/graph_live.json
mosquitto_pub -p 1886 -t openWB/graph/alllivevaluesJson -r -m "$(cat ${OPENWBBASEDIR}/ramdisk/graph_live.json | tail -n 50)" &
mosquitto_pub -p 1886 -t openWB/graph/alllivevaluesJson1 -r -m "$(< ${OPENWBBASEDIR}/ramdisk/graph_live.json tail -n +"0" | head -n "$((50 - 0))")" &
all2livevalues=$(< ${OPENWBBASEDIR}/ramdisk/graph_live.json tail -n +"50" | head -n "$((100 - 50))")
all3livevalues="$(< ${OPENWBBASEDIR}/ramdisk/graph_live.json tail -n +"100" | head -n "$((150 - 100))")"
all4livevalues="$(< ${OPENWBBASEDIR}/ramdisk/graph_live.json tail -n +"150" | head -n "$((200 - 150))")"
all5livevalues="$(< ${OPENWBBASEDIR}/ramdisk/graph_live.json tail -n +"200" | head -n "$((250 - 200))")"
all6livevalues="$(< ${OPENWBBASEDIR}/ramdisk/graph_live.json tail -n +"250" | head -n "$((300 - 250))")"
all7livevalues="$(< ${OPENWBBASEDIR}/ramdisk/graph_live.json tail -n +"300" | head -n "$((350 - 300))")"
all8livevalues="$(< ${OPENWBBASEDIR}/ramdisk/graph_live.json tail -n +"350" | head -n "$((400 - 350))")"
all9livevalues="$(< ${OPENWBBASEDIR}/ramdisk/graph_live.json tail -n +"400" | head -n "$((450 - 400))")"
all10livevalues="$(< ${OPENWBBASEDIR}/ramdisk/graph_live.json tail -n +"450" | head -n "$((500 - 450))")"
all11livevalues="$(< ${OPENWBBASEDIR}/ramdisk/graph_live.json tail -n +"500" | head -n "$((550 - 500))")"
all12livevalues="$(< ${OPENWBBASEDIR}/ramdisk/graph_live.json tail -n +"550" | head -n "$((600 - 550))")"
all13livevalues="$(< ${OPENWBBASEDIR}/ramdisk/graph_live.json tail -n +"600" | head -n "$((650 - 600))")"
all14livevalues="$(< ${OPENWBBASEDIR}/ramdisk/graph_live.json tail -n +"650" | head -n "$((700 - 650))")"
all15livevalues="$(< ${OPENWBBASEDIR}/ramdisk/graph_live.json tail -n +"700" | head -n "$((750 - 700))")"
all16livevalues="$(< ${OPENWBBASEDIR}/ramdisk/graph_live.json tail -n +"750" | head -n "$((800 - 750))")"
mosquitto_pub -p 1886 -t openWB/graph/alllivevaluesJson2 -r -m "$([ ${#all2livevalues} -ge 10 ] && echo "$all2livevalues" || echo "-")" &
mosquitto_pub -p 1886 -t openWB/graph/alllivevaluesJson3 -r -m "$([ ${#all3livevalues} -ge 10 ] && echo "$all3livevalues" || echo "-")" &
mosquitto_pub -p 1886 -t openWB/graph/alllivevaluesJson4 -r -m "$([ ${#all4livevalues} -ge 10 ] && echo "$all4livevalues" || echo "-")" &
mosquitto_pub -p 1886 -t openWB/graph/alllivevaluesJson5 -r -m "$([ ${#all5livevalues} -ge 10 ] && echo "$all5livevalues" || echo "-")" &
mosquitto_pub -p 1886 -t openWB/graph/alllivevaluesJson6 -r -m "$([ ${#all6livevalues} -ge 10 ] && echo "$all6livevalues" || echo "-")" &
mosquitto_pub -p 1886 -t openWB/graph/alllivevaluesJson7 -r -m "$([ ${#all7livevalues} -ge 10 ] && echo "$all7livevalues" || echo "-")" &
mosquitto_pub -p 1886 -t openWB/graph/alllivevaluesJson8 -r -m "$([ ${#all8livevalues} -ge 10 ] && echo "$all8livevalues" || echo "-")" &
mosquitto_pub -p 1886 -t openWB/graph/alllivevaluesJson9 -r -m "$([ ${#all9livevalues} -ge 10 ] && echo "$all9livevalues" || echo "-")" &
mosquitto_pub -p 1886 -t openWB/graph/alllivevaluesJson10 -r -m "$([ ${#all10livevalues} -ge 10 ] && echo "$all10livevalues" || echo "-")" &
mosquitto_pub -p 1886 -t openWB/graph/alllivevaluesJson11 -r -m "$([ ${#all11livevalues} -ge 10 ] && echo "$all11livevalues" || echo "-")" &
mosquitto_pub -p 1886 -t openWB/graph/alllivevaluesJson12 -r -m "$([ ${#all12livevalues} -ge 10 ] && echo "$all12livevalues" || echo "-")" &
mosquitto_pub -p 1886 -t openWB/graph/alllivevaluesJson13 -r -m "$([ ${#all13livevalues} -ge 10 ] && echo "$all13livevalues" || echo "-")" &
mosquitto_pub -p 1886 -t openWB/graph/alllivevaluesJson14 -r -m "$([ ${#all14livevalues} -ge 10 ] && echo "$all14livevalues" || echo "-")" &
mosquitto_pub -p 1886 -t openWB/graph/alllivevaluesJson15 -r -m "$([ ${#all15livevalues} -ge 10 ] && echo "$all15livevalues" || echo "-")" &
mosquitto_pub -p 1886 -t openWB/graph/alllivevaluesJson16 -r -m "$([ ${#all16livevalues} -ge 10 ] && echo "$all16livevalues" || echo "-")" &