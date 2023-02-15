from typing import Optional

# from modules.common.component_setup import ComponentSetup

class MercedesEQSocToken:
    def __init__(self,
                 refresh_token: str = "",
                 access_token: str = "",
                 expires_in: int = 0,
                 id_token: str = "",
                 token_type: str = "") -> None:
        self.refresh_token = refresh_token
        self.access_token = access_token
        self.expires_in = expires_in
        self.id_token = id_token
        self.token_type = token_type


class MercedesEQSocConfiguration:
    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None, vin: Optional[str] = None, callbackurl: Optional[str] = None, token: MercedesEQSocToken = None) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.vin = vin
        self.callbackurl = callbackurl
        self.token = token or MercedesEQSocToken()


class MercedesEQSoc:
    def __init__(self,
                 name: str = "MercedesEQ",
                 type: str = "mercedeseq",
                 configuration: MercedesEQSocConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.configuration = configuration or MercedesEQSocConfiguration()
