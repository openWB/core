from modules.common.abstract_chargepoint import SetupChargepoint


class MqttConfiguration:
    def __init__(self):
        pass


class Mqtt(SetupChargepoint[MqttConfiguration]):
    def __init__(self,
                 name: str = "MQTT-Ladepunkt",
                 type: str = "mqtt",
                 id: int = 0,
                 configuration: MqttConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or MqttConfiguration())
