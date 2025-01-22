from typing import Optional


class ZabbixConfiguration:
    def __init__(self,
                 destination_host: Optional[str] = None,
                 hostname: Optional[str] = None,
                 psk_identifier: Optional[str] = None,
                 psk_key: Optional[str] = None):
        self.destination_host = destination_host
        self.hostname = hostname
        self.psk_identifier = psk_identifier
        self.psk_key = psk_key


class Zabbix:
    def __init__(self,
                 name: str = "openWB (Zabbix)",
                 type: str = "zabbix",
                 configuration: ZabbixConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.configuration = configuration or ZabbixConfiguration()
