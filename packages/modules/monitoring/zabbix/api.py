#!/usr/bin/env python3
import os
from modules.common.abstract_device import DeviceDescriptor
from modules.monitoring.zabbix.config import Zabbix
from modules.common.configurable_monitoring import ConfigurableMonitoring


KEY_PATH = "/etc/zabbix/encrypt.psk"
CONFIG_PATH = "/etc/zabbix/zabbix_agent2.conf"


def set_value(lines, key, value):
    for i, line in enumerate(lines):
        if line.startswith(key):
            lines[i] = f"{key}={value}\n"
            break
    else:
        lines.append(f"{key}={value}\n")


def create_config(config: Zabbix):
    os.system(f"sudo touch {KEY_PATH}")
    os.system(f"sudo chmod 666 {KEY_PATH}")
    os.system(f"sudo chmod 666 {CONFIG_PATH}")
    with open(KEY_PATH, "w") as key_file:
        key_file.write(config.configuration.psk_key)
    with open(CONFIG_PATH, "r+") as config_file:
        lines = config_file.readlines()
        set_value(lines, "ServerActive", config.configuration.destination_host)
        set_value(lines, "Hostname", config.configuration.hostname)
        set_value(lines, "TLSConnect", "psk")
        set_value(lines, "TLSAccept", "psk")
        set_value(lines, "TLSPSKFile", KEY_PATH)
        set_value(lines, "TLSPSKIdentity", config.configuration.psk_identifier)
        config_file.seek(0)
        config_file.writelines(lines)
        config_file.truncate()


def create_monitoring(config: Zabbix):
    def start_monitoring():
        os.system("sudo ./runs/install_zabbix.sh")
        create_config(config)
        os.system("sudo systemctl restart zabbix-agent2")
        os.system("sudo systemctl enable zabbix-agent2")

    def stop_monitoring():
        os.system("sudo systemctl stop zabbix-agent2")
        os.system("sudo systemctl disable zabbix-agent2")
    return ConfigurableMonitoring(start_monitoring, stop_monitoring)


device_descriptor = DeviceDescriptor(configuration_factory=Zabbix)
