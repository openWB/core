from dataclasses import dataclass, field
from typing import Optional


@dataclass
class VoltegoToken:
    access_token: Optional[str] = field(default=None, repr=False)  # don't show in UI
    expires_in: Optional[str] = field(default=None)  # don't show in UI
    created_at: Optional[str] = field(default=None)  # don't show in UI


@dataclass
class VoltegoTariffConfiguration:
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    token: VoltegoToken = field(default_factory=VoltegoToken, compare=False)


@dataclass
class VoltegoTariff:
    name: str = "Voltego"
    type: str = "voltego"
    official: bool = True
    configuration: VoltegoTariffConfiguration = field(default_factory=VoltegoTariffConfiguration)
