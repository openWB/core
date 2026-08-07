from dataclasses import dataclass, field
from typing import Optional


@dataclass
class OctopusEnergyTariffConfiguration:
    email: Optional[str] = None
    accountId: Optional[str] = None
    password: Optional[str] = None


@dataclass
class OctopusEnergyTariff:
    name: str = "Octopus Energy Deutschland"
    type: str = "octopusenergy"
    official: bool = False
    configuration: OctopusEnergyTariffConfiguration = field(default_factory=OctopusEnergyTariffConfiguration)
