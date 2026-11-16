from typing import Optional


class PleosToken:
    def __init__(self,
                 access_token: Optional[str] = None,
                 expires_in: int = 0,
                 created_at: int = 0) -> None:
        self.access_token = access_token
        self.expires_in = expires_in
        self.created_at = created_at


class PleosConfiguration:
    def __init__(self,
                 brand: Optional[str] = None,
                 client_id: Optional[str] = None,
                 client_secret: Optional[str] = None,
                 vin: Optional[str] = None,
                 token: Optional[PleosToken] = None) -> None:
        self.brand = brand
        self.client_id = client_id
        self.client_secret = client_secret
        self.vin = vin
        self.token = token or PleosToken()


class Pleos:
    def __init__(self,
                 name: str = "Pleos (Hyundai/Kia/Genesis)",
                 type: str = "pleos",
                 official: bool = False,
                 configuration: Optional[PleosConfiguration] = None) -> None:
        self.name = name
        self.type = type
        self.official = official
        self.configuration = configuration or PleosConfiguration()
