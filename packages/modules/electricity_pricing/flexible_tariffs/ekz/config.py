from dataclasses import dataclass, field


@dataclass
class EkzTariffConfiguration:
    country: str = "ch"  # Themes zeigen bei "ch" Rp statt ct
    unit: str = "Rp"


@dataclass
class EkzTariff:
    name: str = "EKZ (CH)"
    type: str = "ekz"
    official: bool = False
    configuration: EkzTariffConfiguration = field(default_factory=EkzTariffConfiguration)
