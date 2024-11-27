class ZabbixConfiguration:
    def __init__(self,
                 destination_host: str = "",
                 hostname: str = "",
                 psk_identifier: str = "",
                 psk_key: str = ""):
        self.destination_host = destination_host
        self.hostname = hostname
        self.psk_identifier = psk_identifier
        self.psk_key = psk_key


class Zabbix:
    def __init__(self,
                 name: str = "Zabbix",
                 type: str = "zabbix",
                 configuration: ZabbixConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.configuration = configuration or ZabbixConfiguration()
