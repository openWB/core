from dataclasses import dataclass, field
from typing import Optional


@dataclass
class NissanConnectConfiguration:
    user_id: Optional[str] = field(default=None, repr=False)
    password: Optional[str] = field(default=None, repr=False)
    vin: Optional[str] = field(default=None, repr=False)
    refresh_while_charging: bool = False


@dataclass
class NissanConnect:
    name: str = "Nissan – MyNISSAN EU (experimental)"
    type: str = "nissanconnect"
    official: bool = False
    configuration: NissanConnectConfiguration = None

    def __post_init__(self):
        if self.configuration is None:
            self.configuration = NissanConnectConfiguration()
