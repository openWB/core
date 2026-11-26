from dataclasses import dataclass, field
from typing import ClassVar, Optional


@dataclass
class WestfalenWindToken:
    access_token: Optional[str] = field(default=None, repr=False)  # don't show in UI
    refresh_token: Optional[str] = field(default=None, repr=False)  # don't show in UI
    token_type: Optional[str] = field(default=None)  # don't show in UI
    expires: Optional[int] = field(default=None)  # don't show in UI
    created_at: Optional[float] = field(default=None)  # don't show in UI


@dataclass
class WestfalenWindTariffConfiguration:
    username: Optional[str] = None
    password: Optional[str] = None
    contract_id: Optional[str] = None
    token: WestfalenWindToken = field(default_factory=WestfalenWindToken, compare=False)


@dataclass
class WestfalenWindTariff:
    name: str = "WestfalenWind"
    type: str = "westfalen_wind"
    official: bool = True
    publishes_day_ahead: ClassVar[bool] = False  # um 0 Uhr die Preise des laufenden Tages (letzter Preis für 23:45)
    configuration: WestfalenWindTariffConfiguration = field(default_factory=WestfalenWindTariffConfiguration)
