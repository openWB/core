from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RabotTariffConfiguration:
    customer_number: Optional[str] = None
    contract_number: Optional[str] = None


@dataclass
class RabotTariff:
    name: str = "Rabot"
    type: str = "rabot"
    official: bool = True
    configuration: RabotTariffConfiguration = field(default_factory=RabotTariffConfiguration)
