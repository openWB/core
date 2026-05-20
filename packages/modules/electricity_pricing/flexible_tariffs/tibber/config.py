from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TibberTariffConfiguration:
    token: Optional[str] = None
    home_id: Optional[str] = None
    update_hours: list[int] = field(default_factory=lambda: [14])  # tibber publishes once daily before 14:00
    '''
         dynamische Netzentgelte müssen umgerechnet werden,
         damit der Gesamtpreis nicht um den Normalpreis der Netzentgelte verzerrt wird.
        '''
    includes_grid_fee: bool = True


@dataclass
class TibberTariff:
    name: str = "Tibber"
    type: str = "tibber"
    official: bool = True
    configuration: TibberTariffConfiguration = field(default_factory=TibberTariffConfiguration)
