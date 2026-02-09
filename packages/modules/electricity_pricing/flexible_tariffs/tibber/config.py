from typing import Optional


class TibberTariffConfiguration:
    def __init__(self, token: Optional[str] = None, home_id: Optional[str] = None):
        self.token = token
        self.home_id = home_id


class TibberTariff:
    def __init__(self,
                 name: str = "Tibber",
                 type: str = "tibber",
                 official: bool = True,
                 configuration: TibberTariffConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.official = official
        self.configuration = configuration or TibberTariffConfiguration()
