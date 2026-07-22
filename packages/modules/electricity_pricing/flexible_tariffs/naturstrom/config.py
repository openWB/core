from dataclasses import dataclass, field
from typing import Optional


@dataclass
class NaturstromToken:
    access_token: Optional[str] = field(default=None, repr=False)  # don't show in UI
    refresh_token: Optional[str] = field(default=None, repr=False)  # don't show in UI
    token_type: Optional[str] = field(default=None)  # don't show in UI
    expires: Optional[int] = field(default=None)  # don't show in UI
    created_at: Optional[float] = field(default=None)  # don't show in UI


@dataclass
class NaturstromTariffConfiguration:
    token: NaturstromToken = field(default_factory=NaturstromToken, compare=False)
    account_id: Optional[str] = None
    account_name: Optional[str] = None

    # Rabot publishes once daily at 00:00 for the following day
    update_hours: list[int] = field(default_factory=lambda: [0])


@dataclass
class NaturstromTariff:
    name: str = "Naturstrom"
    type: str = "naturstrom"
    official: bool = True
    configuration: NaturstromTariffConfiguration = field(default_factory=NaturstromTariffConfiguration)
