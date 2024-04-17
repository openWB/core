from typing import Optional


class EnergyChartsTariffConfiguration:
    def __init__(self, country: str = 'de'):
        self.country = country


class EnergyChartsTariff:
    def __init__(self,
                 name: str = "Energy-Charts",
                 type: str = "energycharts",
                 configuration: EnergyChartsTariffConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.configuration = configuration or EnergyChartsTariffConfiguration()
