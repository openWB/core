#!/usr/bin/env python3
import logging
import re
import json
from datetime import datetime
from subprocess import Popen
from pathlib import Path
from time import sleep
from typing import Optional
import paho.mqtt.client as mqtt
import platform


API_VERSION = "1"
BASE_PATH = Path(__file__).resolve().parents[2]
RAMDISK_PATH = BASE_PATH / "ramdisk"
RUNS_PATH = BASE_PATH / "runs"
BASE_TOPIC = "openWB-remote/"
API_TOPIC = BASE_TOPIC + "api_version"
STATE_TOPIC = BASE_TOPIC + "connection_state"
REMOTE_SUPPORT_TOPIC = BASE_TOPIC + "support"
REMOTE_PARTNER_TOPIC = BASE_TOPIC + "partner"
REMOTE_PARTNER_IDS_TOPIC = BASE_TOPIC + "valid_partner_ids"
CLOUD_TOPIC = BASE_TOPIC + "cloud"

mqtt_broker_host = "localhost"
mqtt_broker_port = 1886

support_tunnel: Popen = None
partner_tunnel: Popen = None
cloud_tunnel: Popen = None
valid_partner_ids: list[str] = []
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


def publish_as_json(client: mqtt.Client, topic: str, str_payload: str, qos: int = 0, retain: bool = False,
                    properties: Optional[mqtt.Properties] = None) -> mqtt.MQTTMessageInfo:
    return client.publish(topic, json.dumps(str_payload), qos, retain, properties)


def get_lt_executable() -> Optional[Path]:
    machine = platform.machine()
    bits, linkage = platform.architecture()
    lt_executable = f"lt-{machine}_{linkage}"

    log.debug("System Info:")
    log.debug(f"Architecture: ({(bits, linkage)})")
    log.debug(f"Machine: {machine}")
    log.debug(f"Node: {platform.node()}")
    log.debug(f"Platform: {platform.platform()}")
    log.debug(f"System: {platform.system()}")
    log.debug(f"Release: {platform.release()}")
    log.debug(f"using binary: '{lt_executable}'")

    lt_path = RUNS_PATH / lt_executable
    if not lt_path.is_file():
        log.error(f"file '{lt_executable}' does not exist!")
        return None
    return lt_path


def on_connect(client: mqtt.Client, userdata, flags: dict, rc: int):
    """connect to broker and subscribe to set topics"""
    log.info("Connected")
    client.subscribe([
        (REMOTE_SUPPORT_TOPIC, 2),
        (CLOUD_TOPIC, 2),
        (REMOTE_PARTNER_TOPIC, 2),
        (REMOTE_PARTNER_IDS_TOPIC, 2)
    ])
    publish_as_json(client, API_TOPIC, API_VERSION, qos=2, retain=True)
    publish_as_json(client, STATE_TOPIC, "online", qos=2, retain=True)


def on_message(client: mqtt.Client, userdata, msg: mqtt.MQTTMessage):
    """handle incoming messages"""
    def is_tunnel_closed(tunnel: Popen) -> bool:
        log.debug(str(tunnel))
        is_closed = False
        if tunnel is not None:
            if tunnel.poll() is None:
                log.error("received start tunnel message but tunnel is already running")
            else:
                is_closed = True
                log.info("tunnel was closed by server")
        else:
            is_closed = True
        return is_closed

    global support_tunnel
    global partner_tunnel
    global cloud_tunnel
    global valid_partner_ids
    clear_topic = False
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
            clear_topic = True
        elif msg.topic == REMOTE_PARTNER_IDS_TOPIC:
            valid_partner_ids = json.loads(payload)
        elif msg.topic == REMOTE_PARTNER_TOPIC:
            if payload == 'stop':
                if partner_tunnel is None:
                    log.error("received stop tunnel message but tunnel is not running")
                else:
                    log.info("stop partner support")
                    partner_tunnel.terminate()
                    partner_tunnel.wait(timeout=3)
                    partner_tunnel = None
            elif re.match(r'^([^;]+)(?:;((?:cnode)?[0-9]+)(?:;([\wäöüÄÖÜ-]+))?)?$', payload):
                if is_tunnel_closed(partner_tunnel):
                    splitted = payload.split(";")
                    if len(splitted) != 3:
                        log.error("invalid number of settings received!")
                    else:
                        token = splitted[0]
                        port_or_node = splitted[1]
                        user = splitted[2]  # not used in v0, partner-id in v1
                        if port_or_node.isdecimal():
                            # v0
                            log.info("start partner support")
                            partner_tunnel = Popen(["sshpass", "-p", token, "ssh", "-N", "-tt", "-o",
                                                    "StrictHostKeyChecking=no", "-o", "ServerAliveInterval 60", "-R",
                                                    f"{port_or_node}:localhost:80", f"{user}@partner.openwb.de"])
                            log.info(f"tunnel running with pid {partner_tunnel.pid}")
                        else:
                            # v1
                            if lt_executable is None:
                                log.error("start partner tunnel requested but lt executable not found!")
                            else:
                                if user in valid_partner_ids:
                                    log.info("start partner support v1")
                                    if lt_executable is not None:
                                        partner_tunnel = Popen([f"{lt_executable}", "-h",
                                                                "https://" + port_or_node + ".openwb.de/",
                                                                "-p", "80", "-s", token])
                                        log.info(f"tunnel running with pid {partner_tunnel.pid}")
                                else:
                                    log.error(f"invalid partner-id: {user}")
            else:
                log.info("unknown message: " + payload)
            clear_topic = True
        elif msg.topic == CLOUD_TOPIC:
            if payload == 'stop':
                if cloud_tunnel is None:
                    log.error("received stop cloud message but tunnel is not running")
                else:
                    log.info("stop cloud tunnel")
                    cloud_tunnel.terminate()
                    cloud_tunnel.wait(timeout=3)
                    cloud_tunnel = None
            elif re.match(r'^([^;]+)(?:;([a-zA-Z0-9]+)(?:;([a-zA-Z0-9]+))?)?$', payload):
                if is_tunnel_closed(cloud_tunnel):
                    splitted = payload.split(";")
                    if len(splitted) != 3:
                        log.error("invalid number of settings received!")
                    else:
                        token = splitted[0]
                        cloud_node = splitted[1]
                        user = splitted[2]

                        if lt_executable is None:
                            log.error("start cloud tunnel requested but lt executable not found!")
                        else:
                            log.info(f"start cloud tunnel '{token[:4]}...{token[-4:]}' on '{cloud_node}'")
                            cloud_tunnel = Popen([f"{lt_executable}", "-h",
                                                  "https://" + cloud_node + ".openwb.de/", "-p", "80", "-s", token])
                            log.info(f"cloud tunnel running with pid {cloud_tunnel.pid}")
            else:
                log.info("unknown message: " + payload)
            clear_topic = True
        # clear topic
        if clear_topic and msg.retain:
            client.publish(msg.topic, "", qos=2, retain=True)


lt_executable = get_lt_executable()
client = mqtt.Client(f"openWB-remote-{get_serial()}-{datetime.today().timestamp()}")
client.on_connect = on_connect
client.on_message = on_message
client.will_set(STATE_TOPIC, json.dumps("offline"), qos=2, retain=True)

log.debug("connecting to broker")
client.connect(mqtt_broker_host, mqtt_broker_port)
log.debug("starting loop")
client.loop_start()
try:
    while True:
        sleep(1)
except (Exception, KeyboardInterrupt) as e:
    log.debug(e)
    log.debug("terminated")
finally:
    log.debug("publishing state 'offline'")
    publish_as_json(client, STATE_TOPIC, "offline", qos=2, retain=True)
    sleep(0.5)
    log.debug("stopping loop")
    client.loop_stop()
    client.disconnect()
    log.debug("disconnected")
log.debug("exit")
