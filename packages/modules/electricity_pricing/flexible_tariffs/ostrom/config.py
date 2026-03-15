from typing import Optional


class OstromTariffConfiguration:
    def __init__(self,
                 client_id: Optional[str] = None,
                 client_secret: Optional[str] = None,
                 zip: Optional[str] = None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.zip = zip
        self.update_hours = [2, 8, 14, 20]  # expected time to get next chunk of prices


class OstromTariff:
    def __init__(self,
                 name: str = "ostrom",
                 type: str = "ostrom",
                 official: bool = False,
                 configuration: OstromTariffConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.official = official
        self.configuration = configuration or OstromTariffConfiguration()
