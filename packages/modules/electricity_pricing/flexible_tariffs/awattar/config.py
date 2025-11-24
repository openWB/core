class AwattarTariffConfiguration:
    def __init__(self, country: str = "de", net: bool = True, fix: float = 0.015, proportional: float = 3, tax: float = 20) -> None:
        self.country = country
        self.net = net
        self.fix = fix
        self.proportional = proportional
        self.tax = tax


class AwattarTariff:
    def __init__(self,
                 name: str = "aWATTar/tado° HOURLY",
                 type: str = "awattar",
                 official: bool = True,
                 configuration: AwattarTariffConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.official = official
        self.configuration = configuration or AwattarTariffConfiguration()
