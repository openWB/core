class AwattarTariffConfiguration:
    def __init__(self, country: str = "de"):
        self.country = country


class AwattarTariff:
    def __init__(self,
                 name: str = "aWATTar Hourly",
                 type: str = "awattar",
                 configuration: AwattarTariffConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.configuration = configuration or AwattarTariffConfiguration()
