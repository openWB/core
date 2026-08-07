from dataclasses import dataclass, field


@dataclass
class AwattarTariffConfiguration:
    country: str = "de"
    net: bool = True
    fix: float = 0.000015
    proportional: float = 3
    tax: float = 20


@dataclass
class AwattarTariff:
    name: str = "aWATTar/tado° HOURLY"
    type: str = "awattar"
    official: bool = True
    configuration: AwattarTariffConfiguration = field(default_factory=AwattarTariffConfiguration)
