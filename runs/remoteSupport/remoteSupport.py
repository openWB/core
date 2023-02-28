#!/usr/bin/env python3
import logging
import re
import subprocess
from pathlib import Path
import paho.mqtt.client as mqtt

BASE_PATH = Path(__file__).resolve().parents[2]
RAMDISK_PATH = BASE_PATH / "ramdisk"

logging.basicConfig(
    filename=str(RAMDISK_PATH / "remote_support.log"),
    level=logging.DEBUG, format='%(asctime)s: %(message)s'
)
log = logging.getLogger("RemoteSupport")


def get_serial():
    """Extract serial from cpuinfo file"""
    with open('/proc/cpuinfo', 'r') as f:
        for line in f:
            if line[0:6] == 'Serial':
                return line[10:26]
        return "0000000000000000"


def on_connect(client: mqtt.Client, userdata, flags: dict, rc: int):
    """connect to broker and subscribe to set topics"""
    log.info("Connected")
    client.subscribe("openWB/set/system/GetRemoteSupport", 2)


def on_message(client: mqtt.Client, userdata, msg: mqtt.MQTTMessage):
    """handle incoming messages"""
    payload = msg.payload.decode("utf-8")
    if msg.topic == "openWB/set/system/GetRemoteSupport" and len(payload) >= 1:
        log.info("Topic: %s, Message: %s", msg.topic, payload)

        if payload == 'stop':
            log.info("stop remote support: " + str(BASE_PATH / "runs" / "remoteSupport" / "stopRemoteSupport.sh"))
            subprocess.run([str(BASE_PATH / "runs" / "remoteSupport" / "stopRemoteSupport.sh")])
        elif re.match(r'^[A-Za-z0-9]+;[1-9][0-9]+(;[a-zA-Z0-9]+)?$', payload):
            log.info("token file: " + str(RAMDISK_PATH / "remote_support.token"))
            with open(str(RAMDISK_PATH / "remote_support.token"), "w") as file:
                file.write(payload)
            log.info("init remote support: " + str(BASE_PATH / "runs" / "remoteSupport" / "initRemoteSupport.sh"))
            subprocess.run([str(BASE_PATH / "runs" / "remoteSupport" / "initRemoteSupport.sh")])
        else:
            log.info("unknown message: " + payload)
        # clear topic
        client.publish(msg.topic, "", qos=2, retain=True)


mqtt_broker_host = "localhost"
client = mqtt.Client("openWB-remote-support-" + get_serial())
client.on_connect = on_connect
client.on_message = on_message

client.connect(mqtt_broker_host, 1883)
client.loop_forever()
client.disconnect()
