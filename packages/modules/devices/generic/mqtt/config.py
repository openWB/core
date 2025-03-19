#!/usr/bin/env python3
from modules.common.component_setup import ComponentSetup
from ..vendor import vendor_descriptor


class MqttConfiguration:
    def __init__(self):
        pass


class Mqtt:
    def __init__(self,
                 name: str = "MQTT",
                 type: str = "mqtt",
                 id: int = 0,
                 configuration: MqttConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or MqttConfiguration()


class MqttBatConfiguration:
    def __init__(self):
        pass


class MqttBatSetup(ComponentSetup[MqttBatConfiguration]):
    def __init__(self,
                 name: str = "MQTT-Speicher",
                 type: str = "bat",
                 id: int = 0,
                 configuration: MqttBatConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or MqttBatConfiguration())


class MqttCounterConfiguration:
    def __init__(self):
        pass


class MqttCounterSetup(ComponentSetup[MqttCounterConfiguration]):
    def __init__(self,
                 name: str = "MQTT-Zähler",
                 type: str = "counter",
                 id: int = 0,
                 configuration: MqttCounterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or MqttCounterConfiguration())


class MqttInverterConfiguration:
    def __init__(self):
        pass


class MqttInverterSetup(ComponentSetup[MqttInverterConfiguration]):
    def __init__(self,
                 name: str = "MQTT-Wechselrichter",
                 type: str = "inverter",
                 id: int = 0,
                 configuration: MqttInverterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or MqttInverterConfiguration())
