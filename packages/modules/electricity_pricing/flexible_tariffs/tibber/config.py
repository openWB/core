from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TibberTariffConfiguration:
    token: Optional[str] = None
    home_id: Optional[str] = None
    # dynamische Netzentgelte müssen umgerechnet werden,
    # damit der Gesamtpreis nicht um den Normalpreis der Netzentgelte verzerrt wird.
    includes_grid_fee: bool = True


@dataclass
class TibberTariff:
    name: str = "Tibber"
    type: str = "tibber"
    official: bool = True
    configuration: TibberTariffConfiguration = field(default_factory=TibberTariffConfiguration)
