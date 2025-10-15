#!/usr/bin/python3
import sys
import time
import paho.mqtt.client as mqtt
numberOfSupportedDevices = 9  # limit number of smart home devices


def on_connect(client, userdata, flags, rc) -> None:
    client.subscribe("openWB/set/LegacySmartHome/Devices/#", 2)


def on_message(client, userdata, msg) -> None:
    global numberOfSupportedDevices


devicenumber = str(sys.argv[1])
ipadr = str(sys.argv[2])
uberschuss = int(sys.argv[3])
client = mqtt.Client("openWB-mqttsmarthomecust")
client.on_connect = on_connect
client.on_message = on_message
startTime = time.time()
waitTime = 2
client.connect("localhost")
while True:
    client.loop()
    elapsedTime = time.time() - startTime
    if elapsedTime > waitTime:
        break
client.publish("openWB/set/LegacySmartHome/Devices/"+str(devicenumber)+"/ReqRelay", "1", qos=0, retain=True)
client.loop(timeout=2.0)
client.publish("openWB/set/LegacySmartHome/Devices/"+str(devicenumber) +
               "/Ueberschuss", payload=str(uberschuss), qos=0, retain=True)
client.loop(timeout=2.0)
client.disconnect()
file_stringpv = '/var/www/html/openWB/ramdisk/smarthome_device_' + str(devicenumber) + '_pv'
f = open(file_stringpv, 'w')
f.write(str(1))
f.close()
