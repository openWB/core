#!/usr/bin/python3
import sys
import time
import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion
from paho.mqtt.reasoncodes import ReasonCode as MqttReasonCode
from paho.mqtt.properties import Properties as MqttProperties
from typing import Optional
numberOfSupportedDevices = 9  # limit number of smart home devices


def on_connect(client: mqtt.Client, userdata, flags: mqtt.ConnectFlags, reason_code: MqttReasonCode, properties: Optional[MqttProperties]) -> None:
    client.subscribe("openWB/set/LegacySmartHome/Devices/#", 2)


def on_message(client: mqtt.Client, userdata, msg: mqtt.MQTTMessage) -> None:
    pass  # No action needed for incoming messages in this script


devicenumber = str(sys.argv[1])
ipadr = str(sys.argv[2])
uberschuss = int(sys.argv[3])
client = mqtt.Client(
    callback_api_version=CallbackAPIVersion.VERSION2,
    client_id="openWB-mqttsmarthomecust",
)
client.on_connect = on_connect
client.on_message = on_message
startTime = time.time()
waitTime = 2
client.connect(host="localhost", port=1886)
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
with open(file_stringpv, 'w') as f:
    f.write(str(1))
