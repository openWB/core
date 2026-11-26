from dataclasses import dataclass, field
from typing import ClassVar


@dataclass
class EkzTariffConfiguration:
    country: str = "ch"
    unit: str = "Rp"


@dataclass
class EkzTariff:
    name: str = "EKZ (CH)"
    type: str = "ekz"
    official: bool = False
    first_try_hour: ClassVar[int] = 18  # EKZ liefert die Preise des Folgetags ab 18 Uhr
    configuration: EkzTariffConfiguration = field(default_factory=EkzTariffConfiguration)
