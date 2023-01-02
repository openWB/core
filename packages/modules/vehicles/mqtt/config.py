class MqttSocConfiguration:
    def __init__(self):
        pass


class MqttSocSetup:
    def __init__(self,
                 name: str = "mqtt",
                 type: str = "mqtt",
                 id: int = 0,
                 configuration: MqttSocConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.id = id
        self.configuration = configuration or MqttSocConfiguration()
