from typing import Optional


class RabotToken():
    def __init__(self,
                 access_token: Optional[str] = None,
                 expires_in: Optional[str] = None,
                 created_at: Optional[str] = None) -> None:
        self.access_token = access_token  # don't show in UI
        self.expires_in = expires_in  # don't show in UI
        self.created_at = created_at  # don't show in UI


class RabotTariffConfiguration:
    def __init__(self,
                 client_id: Optional[str] = None,
                 client_secret: Optional[str] = None,
                 token: RabotToken = None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = token or RabotToken()


class RabotTariff:
    def __init__(self,
                 name: str = "Rabot",
                 type: str = "rabot",
                 configuration: RabotTariffConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.configuration = configuration or RabotTariffConfiguration()
