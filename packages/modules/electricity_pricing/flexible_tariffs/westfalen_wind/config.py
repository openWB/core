from typing import Optional


class WestfalenWindToken():
    def __init__(self,
                 access_token: Optional[str] = None,
                 refresh_token: Optional[str] = None,
                 token_type: Optional[str] = None,
                 expires: Optional[int] = None,
                 created_at: Optional[float] = None) -> None:
        self.access_token = access_token  # don't show in UI
        self.refresh_token = refresh_token  # don't show in UI
        self.token_type = token_type  # don't show in UI
        self.expires = expires  # don't show in UI
        self.created_at = created_at  # don't show in UI


class WestfalenWindTariffConfiguration:
    def __init__(self,
                 username: Optional[str] = None,
                 password: Optional[str] = None,
                 contract_id: Optional[str] = None,
                 token: WestfalenWindToken = None):
        self.username = username
        self.password = password
        self.contract_id = contract_id
        self.token = token or WestfalenWindToken()


class WestfalenWindTariff:
    def __init__(self,
                 name: str = "WestfalenWind",
                 type: str = "westfalen_wind",
                 official: bool = True,
                 configuration: WestfalenWindTariffConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.official = official
        self.configuration = configuration or WestfalenWindTariffConfiguration()
