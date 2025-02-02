from typing import Optional

class OstromTariffConfiguration:
    def __init__(self,
                 client_id: Optional[str] = None,
                 client_secret: Optional[str] = None,
                 zip: Optional[str] = None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.zip = zip


class OstromTariff:
    def __init__(self,
                 name: str = "ostrom",
                 type: str = "ostrom",
                 configuration: OstromTariffConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.configuration = configuration or OstromTariffConfiguration()
