from typing import Optional


class VoltegoToken():
    def __init__(self,
                 access_token: Optional[str] = None,
                 expires_in: Optional[str] = None,
                 created_at: Optional[str] = None) -> None:
        self.access_token = access_token  # don't show in UI
        self.expires_in = expires_in  # don't show in UI
        self.created_at = created_at  # don't show in UI


class VoltegoTariffConfiguration:
    def __init__(self,
                 client_id: Optional[str] = None,
                 client_secret: Optional[str] = None,
                 token: VoltegoToken = None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = token or VoltegoToken()


class VoltegoTariff:
    def __init__(self,
                 name: str = "Voltego",
                 type: str = "voltego",
                 configuration: VoltegoTariffConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.configuration = configuration or VoltegoTariffConfiguration()
