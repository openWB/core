from typing import Optional


class TeslaSocToken:
    def __init__(self,
                 refresh_token: Optional[str] = None,
                 access_token: Optional[str] = None,
                 expires_in: int = 0,
                 created_at: int = 0) -> None:
        self.refresh_token = refresh_token
        self.access_token = access_token
        self.expires_in = expires_in
        self.created_at = created_at


class TeslaSocConfiguration:
    def __init__(self, tesla_ev_num: int = 0, token: TeslaSocToken = None) -> None:
        self.tesla_ev_num = tesla_ev_num
        self.token = token or TeslaSocToken()


class TeslaSoc:
    def __init__(self,
                 name: str = "Tesla",
                 type: str = "tesla",
                 configuration: TeslaSocConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.configuration = configuration or TeslaSocConfiguration()
