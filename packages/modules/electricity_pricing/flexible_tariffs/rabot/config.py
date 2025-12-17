from typing import Optional


class RabotTariffConfiguration:
    def __init__(self,
                 costumer_number: Optional[str] = None,
                 contract_number: Optional[str] = None):
        self.costumer_number = costumer_number
        self.contract_number = contract_number


class RabotTariff:
    def __init__(self,
                 name: str = "Rabot",
                 type: str = "rabot",
                 official: bool = True,
                 configuration: RabotTariffConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.official = official
        self.configuration = configuration or RabotTariffConfiguration()
