class MqttSocConfiguration:
    def __init__(self):
        pass


class MqttSocSetup:
    def __init__(self,
                 name: str = "MQTT",
                 type: str = "mqtt",
                 official: bool = True,
                 configuration: MqttSocConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.official = official
        self.configuration = configuration or MqttSocConfiguration()
