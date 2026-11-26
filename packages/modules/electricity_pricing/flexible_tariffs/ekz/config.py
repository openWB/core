from dataclasses import dataclass, field


@dataclass
class EkzTariffConfiguration:
    pass


@dataclass
class EkzTariff:
    name: str = "EKZ (CH)"
    type: str = "ekz"
    official: bool = False
    configuration: EkzTariffConfiguration = field(default_factory=EkzTariffConfiguration)
