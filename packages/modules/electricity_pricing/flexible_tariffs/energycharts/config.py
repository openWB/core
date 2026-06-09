from dataclasses import dataclass, field


@dataclass
class EnergyChartsTariffConfiguration:
    country: str = "DE-LU"
    surcharge: float = 0
    net: bool = True
    tax: float = 19


@dataclass
class EnergyChartsTariff:
    name: str = "Energy-Charts"
    type: str = "energycharts"
    official: bool = True
    configuration: EnergyChartsTariffConfiguration = field(default_factory=EnergyChartsTariffConfiguration)
