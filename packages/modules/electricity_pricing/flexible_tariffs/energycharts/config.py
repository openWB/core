class EnergyChartsTariffConfiguration:
    def __init__(self, country: str = "DE-LU", surcharge: float = 0):
        self.country = country
        self.surcharge = surcharge


class EnergyChartsTariff:
    def __init__(self,
                 name: str = "Energy-Charts",
                 type: str = "energycharts",
                 official: bool = True,
                 configuration: EnergyChartsTariffConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.official = official
        self.configuration = configuration or EnergyChartsTariffConfiguration()
