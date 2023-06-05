#!/usr/bin/env python3
import logging
import re
from subprocess import Popen
from pathlib import Path
import paho.mqtt.client as mqtt

BASE_PATH = Path(__file__).resolve().parents[2]
RAMDISK_PATH = BASE_PATH / "ramdisk"
BASE_TOPIC = "openWB-remote/"
REMOTE_SUPPORT_TOPIC = BASE_TOPIC + "support"
REMOTE_PARTNER_TOPIC = BASE_TOPIC + "partner"
support_tunnel: Popen = None
partner_tunnel: Popen = None

logging.basicConfig(
    filename=str(RAMDISK_PATH / "remote_support.log"),
    level=logging.INFO, format='%(asctime)s: %(message)s'
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
    client.subscribe(BASE_TOPIC + "#", 2)


def on_message(client: mqtt.Client, userdata, msg: mqtt.MQTTMessage):
    """handle incoming messages"""
    def is_tunnel_closed(tunnel: Popen) -> bool:
        start = False
        if tunnel is not None:
            if tunnel.poll() is None:
                start = True
                log.info("tunnel was closed by server")
            else:
                log.error("received start tunnel message but tunnel is already running")
        else:
            start = True
        return start

    global support_tunnel
    global partner_tunnel
    payload = msg.payload.decode("utf-8")
    if len(payload) > 0:
        log.debug("Topic: %s, Message: %s", msg.topic, payload)
        if msg.topic == REMOTE_SUPPORT_TOPIC:
            if payload == 'stop':
                if support_tunnel is None:
                    log.error("received stop tunnel message but tunnel is not running")
                else:
                    log.info("stop remote support")
                    support_tunnel.terminate()
                    support_tunnel.wait(timeout=3)
                    support_tunnel = None
            elif re.match(r'^([^;]+)(?:;([1-9][0-9]+)(?:;([a-zA-Z0-9]+))?)?$', payload):
                if is_tunnel_closed(support_tunnel):
                    splitted = payload.split(";")
                    token = splitted[0]
                    port = splitted[1] if len(splitted) > 1 else "2223"
                    user = splitted[2] if len(splitted) > 2 else "getsupport"
                    log.info("start remote support")
                    support_tunnel = Popen(["sshpass", "-p", token, "ssh", "-N", "-tt", "-o",
                                            "StrictHostKeyChecking=no", "-o", "ServerAliveInterval 60", "-R",
                                            f"{port}:localhost:22", f"{user}@remotesupport.openwb.de"])
                    log.info(f"tunnel running with pid {support_tunnel.pid}")
            else:
                log.info("unknown message: " + payload)
        elif msg.topic == REMOTE_PARTNER_TOPIC:
            if payload == 'stop':
                if partner_tunnel is None:
                    log.error("received stop tunnel message but tunnel is not running")
                else:
                    log.info("stop partner support")
                    partner_tunnel.terminate()
                    partner_tunnel.wait(timeout=3)
                    partner_tunnel = None
            elif re.match(r'^([^;]+)(?:;([1-9][0-9]+)(?:;([a-zA-Z0-9]+))?)?$', payload):
                if is_tunnel_closed(partner_tunnel):
                    splitted = payload.split(";")
                    if len(splitted) != 3:
                        log.error("invalid number of settings received!")
                    else:
                        token = splitted[0]
                        port = splitted[1]
                        user = splitted[2]
                        log.info("start partner support")
                        partner_tunnel = Popen(["sshpass", "-p", token, "ssh", "-N", "-tt", "-o",
                                                "StrictHostKeyChecking=no", "-o", "ServerAliveInterval 60", "-R",
                                                f"{port}:localhost:80", f"{user}@partner.openwb.de"])
                        log.info(f"tunnel running with pid {partner_tunnel.pid}")
            else:
                log.info("unknown message: " + payload)
        # clear topic
        client.publish(msg.topic, "", qos=2, retain=True)


mqtt_broker_host = "localhost"
client = mqtt.Client("openWB-remote-" + get_serial())
client.on_connect = on_connect
client.on_message = on_message

client.connect(mqtt_broker_host, 1883)
client.loop_forever()
client.disconnect()
