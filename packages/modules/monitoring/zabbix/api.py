#!/usr/bin/env python3
import os
from modules.common.abstract_device import DeviceDescriptor
from modules.monitoring.zabbix.config import Zabbix


KEY_PATH = "/etc/zabbix/encrypt.psk"
CONFIG_PATH = "/etc/zabbix/zabbix_agent2.conf"


def set_value(path, key, value):
    with open(path, "r+") as file:
        lines = file.readlines()
        for i, line in enumerate(lines):
            if line.startswith(key):
                lines[i] = f"{key}={value}\n"
                break
        else:
            lines.append(f"{key}={value}\n")
        file.seek(0)
        file.writelines(lines)
        file.truncate()


def create_config(config: Zabbix):
    os.system(f"sudo touch {KEY_PATH}")
    os.system(f"sudo chmod 666 {KEY_PATH}")
    os.system(f"sudo chmod 666 {CONFIG_PATH}")
    with open(KEY_PATH, "w") as key_file:
        key_file.write(config.configuration.psk_key)
    set_value(CONFIG_PATH, "ServerActive", config.configuration.destination_host)
    set_value(CONFIG_PATH, "Hostname", config.configuration.hostname)
    set_value(CONFIG_PATH, "TLSConnect", "psk")
    set_value(CONFIG_PATH, "TLSAccept", "psk")
    set_value(CONFIG_PATH, "TLSPSKFile", KEY_PATH)
    set_value(CONFIG_PATH, "TLSPSKIdentity", config.configuration.psk_identifier)


device_descriptor = DeviceDescriptor(configuration_factory=Zabbix)
