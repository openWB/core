"""Native openWB configuration; credentials follow its existing storage lifecycle."""
from typing import Optional


class NissanConnectConfiguration:
    """EU account credentials and optional VIN; never log or export this object."""

    def __init__(self, user_id: Optional[str] = None, password: Optional[str] = None,
                 vin: Optional[str] = None):
        self.user_id = user_id
        self.password = password
        self.vin = vin


class NissanConnect:
    """Descriptor defaults consumed by the standard module loader and settings UI."""

    def __init__(self, name: str = "Nissan – MyNISSAN EU (experimental)",
                 type: str = "nissanconnect", configuration: NissanConnectConfiguration = None):
        self.name = name
        self.type = type
        self.configuration = configuration or NissanConnectConfiguration()
