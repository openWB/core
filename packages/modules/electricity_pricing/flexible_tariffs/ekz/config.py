from dataclasses import dataclass, field


@dataclass
class EkzTariffConfiguration:
    country: str = "ch"
    unit: str = "Rp"
    update_hours: list[int] = field(default_factory=lambda: [18, 19])


@dataclass
class EkzTariff:
    name: str = "EKZ (CH)"
    type: str = "ekz"
    official: bool = False
    configuration: EkzTariffConfiguration = field(default_factory=EkzTariffConfiguration)
