from dataclasses import dataclass, field
from typing import Optional


@dataclass
class OstromTariffConfiguration:
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    zip: Optional[str] = None
    update_hours: list[int] = field(default_factory=lambda: [2, 8, 14, 20])  # expected time to get next chunk of prices


@dataclass
class OstromTariff:
    name: str = "ostrom"
    type: str = "ostrom"
    official: bool = False
    configuration: OstromTariffConfiguration = field(default_factory=OstromTariffConfiguration)
