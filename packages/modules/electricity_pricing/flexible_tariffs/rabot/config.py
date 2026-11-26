from dataclasses import dataclass, field
from typing import ClassVar, Optional


@dataclass
class RabotTariffConfiguration:
    customer_number: Optional[str] = None
    contract_number: Optional[str] = None


@dataclass
class RabotTariff:
    name: str = "Rabot"
    type: str = "rabot"
    official: bool = True
    publishes_day_ahead: ClassVar[bool] = False  # Rabot veröffentlicht um 0 Uhr die Preise des laufenden Tages
    configuration: RabotTariffConfiguration = field(default_factory=RabotTariffConfiguration)
