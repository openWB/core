#!/usr/bin/env python3
from modules.common.abstract_device import DeviceDescriptor
from modules.zabbix.config import Zabbix


def create_config_files(config: Zabbix):
    key_file = open("/etc/zabbix/encrypt.psk", "w")
    key_file.write(config.configuration.psk_key)
    key_file.close()


device_descriptor = DeviceDescriptor(configuration_factory=Zabbix)
