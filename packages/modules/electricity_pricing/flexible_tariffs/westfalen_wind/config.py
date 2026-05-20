from dataclasses import dataclass, field
from typing import Optional


@dataclass
class WestfalenWindToken:
    access_token: Optional[str] = field(default=None, compare=False, repr=False)  # don't show in UI
    refresh_token: Optional[str] = field(default=None, compare=False, repr=False)  # don't show in UI
    token_type: Optional[str] = field(default=None, compare=False)  # don't show in UI
    expires: Optional[int] = field(default=None, compare=False)  # don't show in UI
    created_at: Optional[float] = field(default=None, compare=False)  # don't show in UI


@dataclass
class WestfalenWindTariffConfiguration:
    username: Optional[str] = None
    password: Optional[str] = None
    contract_id: Optional[str] = None
    token: WestfalenWindToken = field(default_factory=WestfalenWindToken)


@dataclass
class WestfalenWindTariff:
    name: str = "WestfalenWind"
    type: str = "westfalen_wind"
    official: bool = True
    configuration: WestfalenWindTariffConfiguration = field(default_factory=WestfalenWindTariffConfiguration)
