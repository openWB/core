from dataclasses import dataclass, field
from typing import Optional


@dataclass
class EnergyChartsTariffConfiguration:
    country: str = "DE-LU"
    surcharge: float = 0
    net: bool = True
    tax: float = 19
    price_cap: Optional[float] = None


@dataclass
class EnergyChartsTariff:
    name: str = "Energy-Charts"
    type: str = "energycharts"
    official: bool = True
    configuration: EnergyChartsTariffConfiguration = field(default_factory=EnergyChartsTariffConfiguration)
