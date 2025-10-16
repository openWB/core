#!/usr/bin/python3
import sys
import time
import paho.mqtt.client as mqtt
import re
import os
from smarthome.smartret import writeret
numberOfSupportedDevices = 9  # limit number of smart home devices


def on_connect(client, userdata, flags, rc) -> None:
    global devicenumber
    client.subscribe("openWB/LegacySmartHome/Devices/"+str(devicenumber) + "/#", 2)


def on_message(client, userdata, msg) -> None:
    global numberOfSupportedDevices
    global aktpower
    global powerc
    global tempa
    global tempb
    global tempc
    if (("openWB/LegacySmartHome/Device" in msg.topic) and ("Aktpower" in msg.topic)):
        devicenumb = re.sub(r'\D', '', msg.topic)
        if (1 <= int(devicenumb) <= numberOfSupportedDevices):
            aktpower = int(msg.payload)
    if (("openWB/LegacySmartHome/Device" in msg.topic) and ("Powerc" in msg.topic)):
        devicenumb = re.sub(r'\D', '', msg.topic)
        if (1 <= int(devicenumb) <= numberOfSupportedDevices):
            powerc = int(msg.payload)
    if (("openWB/LegacySmartHome/Device" in msg.topic) and ("Tempa" in msg.topic)):
        devicenumb = re.sub(r'\D', '', msg.topic)
        if (1 <= int(devicenumb) <= numberOfSupportedDevices):
            tempa = str(float(msg.payload))
    if (("openWB/LegacySmartHome/Device" in msg.topic) and ("Tempb" in msg.topic)):
        devicenumb = re.sub(r'\D', '', msg.topic)
        if (1 <= int(devicenumb) <= numberOfSupportedDevices):
            tempb = str(float(msg.payload))
    if (("openWB/LegacySmartHome/Device" in msg.topic) and ("Tempc" in msg.topic)):
        devicenumb = re.sub(r'\D', '', msg.topic)
        if (1 <= int(devicenumb) <= numberOfSupportedDevices):
            tempc = str(float(msg.payload))


aktpower = 0
powerc = 0
tempa = '300.00'
tempb = '300.00'
tempc = '300.00'
devicenumber = int(sys.argv[1])
ipadr = str(sys.argv[2])
uberschuss = int(sys.argv[3])
client = mqtt.Client("openWB-mqttsmarthomecust" + str(devicenumber))
client.on_connect = on_connect
client.on_message = on_message
startTime = time.time()
waitTime = 5
client.connect("localhost")
while True:
    client.loop()
    elapsedTime = time.time() - startTime
    if elapsedTime > waitTime:
        break
client.publish("openWB/set/LegacySmartHome/Devices/"+str(devicenumber) +
               "/Ueberschuss", payload=str(uberschuss), qos=0, retain=True)
client.loop(timeout=2.0)
client.disconnect()
file_stringpv = '/var/www/html/openWB/ramdisk/smarthome_device_' + str(devicenumber) + '_pv'
# PV-Modus
pvmodus = 0
if os.path.isfile(file_stringpv):
    with open(file_stringpv, 'r') as f:
        pvmodus = int(f.read())
answer = '{"power":' + str(aktpower) + ',"powerc":' + str(powerc)
answer += ',"on":' + str(pvmodus) + ',"temp0":' + str(tempa)
answer += ',"temp1":' + str(tempb) + ',"temp2":' + str(tempc) + '}'
writeret(answer, devicenumber)
