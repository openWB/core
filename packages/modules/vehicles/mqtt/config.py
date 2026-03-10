class MqttSocConfiguration:
    def __init__(self, calculate_soc: bool = False):
        self.calculate_soc = calculate_soc


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
