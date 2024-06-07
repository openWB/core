from typing import Optional


class RabotTariffConfiguration:
    def __init__(self, token: Optional[str] = None):
        self.token = token


class RabotTariff:
    def __init__(self,
                 name: str = "Rabot",
                 type: str = "rabot",
                 configuration: RabotTariffConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.configuration = configuration or RabotTariffConfiguration()
