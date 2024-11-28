#!/usr/bin/env python3
import re
from helpermodules.utils.run_command import run_command
from modules.common.abstract_device import DeviceDescriptor
from modules.zabbix.config import Zabbix


key_path = "/etc/zabbix/encrypt.psk"
config_path = "/etc/zabbix/zabbix_agent2.conf"


def add_value(path, key, value):
    file = open(path, "r+")
    config = file.read()
    pattern = "\n"+key+"=.*"
    line = "\n"+key + "="+value
    splitted = re.split(pattern, config)

    if splitted.len() == 1:
        splitted.push(line)
        file.writelines(splitted)
        file.close()
    else:
        modified_config = line.join(splitted)
        file.write(modified_config)
        file.close()


def create_config(config: Zabbix):
    key_file = open(key_path, "w")
    key_file.write(config.configuration.psk_key)
    key_file.close()
    add_value(config_path, "ServerActive", config.configuration.destination_host)
    add_value(config_path, "Hostname", config.configuration.hostname)
    add_value(config_path, "TLSConnect", "psk")
    add_value(config_path, "TLSAccept", "psk")
    add_value(config_path, "TLSPSKFile", key_path)
    add_value(config_path, "TLSPSKIdentity", config.configuration.psk_identifier)
    # restart service
    run_command(["sudo systemctl restart zabbix-agent2"], process_exception=True)


device_descriptor = DeviceDescriptor(configuration_factory=Zabbix)
