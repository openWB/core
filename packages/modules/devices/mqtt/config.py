class MqttConfiguration:
    def __init__(self):
        pass


class Mqtt:
    def __init__(self,
                 name: str = "MQTT",
                 type: str = "mqtt",
                 group: str = "generic",
                 device: str = "Alle Geräte",
                 id: int = 0,
                 configuration: MqttConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.group = group
        self.device = device
        self.id = id
        self.configuration = configuration or MqttConfiguration()


class MqttBatConfiguration:
    def __init__(self):
        pass


class MqttBatSetup:
    def __init__(self,
                 name: str = "MQTT-Speicher",
                 type: str = "bat",
                 id: int = 0,
                 configuration: MqttBatConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.id = id
        self.configuration = configuration or MqttBatConfiguration()


class MqttCounterConfiguration:
    def __init__(self):
        pass


class MqttCounterSetup:
    def __init__(self,
                 name: str = "MQTT-Zähler",
                 type: str = "counter",
                 id: int = 0,
                 configuration: MqttCounterConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.id = id
        self.configuration = configuration or MqttCounterConfiguration()


class MqttInverterConfiguration:
    def __init__(self):
        pass


class MqttInverterSetup:
    def __init__(self,
                 name: str = "MQTT-Wechselrichter",
                 type: str = "inverter",
                 id: int = 0,
                 configuration: MqttInverterConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.id = id
        self.configuration = configuration or MqttInverterConfiguration()
