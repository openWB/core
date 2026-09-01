from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RabotTariffConfiguration:
    customer_number: Optional[str] = None
    contract_number: Optional[str] = None
    # Rabot publishes once daily at 00:00 for the following day
    update_hours: list[int] = field(default_factory=lambda: [0])


@dataclass
class RabotTariff:
    name: str = "Rabot"
    type: str = "rabot"
    official: bool = True
    configuration: RabotTariffConfiguration = field(default_factory=RabotTariffConfiguration)
