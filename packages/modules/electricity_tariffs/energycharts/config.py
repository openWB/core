
class EnergyChartsTariffConfiguration:
    def __init__(self, country: str = 'de', serve_price: float = 0):
        self.country = country
        self.serve_price = serve_price


class EnergyChartsTariff:
    def __init__(self,
                 name: str = "Energy-Charts",
                 type: str = "energycharts",
                 configuration: EnergyChartsTariffConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.configuration = configuration or EnergyChartsTariffConfiguration()
