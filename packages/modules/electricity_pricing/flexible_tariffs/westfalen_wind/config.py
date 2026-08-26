from dataclasses import dataclass, field
from typing import Optional


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
    update_hours: list[int] = field(default_factory=lambda: [0])  # letzter Preis für 23:45


@dataclass
class WestfalenWindTariff:
    name: str = "WestfalenWind"
    type: str = "westfalen_wind"
    official: bool = True
    configuration: WestfalenWindTariffConfiguration = field(default_factory=WestfalenWindTariffConfiguration)
