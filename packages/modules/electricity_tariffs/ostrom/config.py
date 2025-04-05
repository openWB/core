from typing import Optional


class OstromToken():
    def __init__(self,
                 access_token: Optional[str] = None,
                 expires_in: Optional[str] = None,
                 created_at: Optional[str] = None) -> None:
        self.access_token = access_token
        self.expires_in = expires_in
        self.created_at = created_at


class OstromTariffConfiguration:
    def __init__(self,
                 client_id: Optional[str] = None,
                 client_secret: Optional[str] = None,
                 zip: Optional[str] = None,
                 token: OstromToken = None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.zip = zip
        self.token = token or OstromToken()


class OstromTariff:
    def __init__(self,
                 name: str = "ostrom",
                 type: str = "ostrom",
                 configuration: OstromTariffConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.configuration = configuration or OstromTariffConfiguration()
