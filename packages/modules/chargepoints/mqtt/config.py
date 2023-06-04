class MqttConfiguration:
    def __init__(self):
        pass


class Mqtt:
    def __init__(self,
                 name: str = "MQTT-Ladepunkt",
                 type: str = "mqtt",
                 id: int = 0,
                 configuration: MqttConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.id = id
        self.configuration = configuration or MqttConfiguration()
