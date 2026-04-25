from dataclasses import dataclass


@dataclass
class BmwCardataConfiguration:
    client_id: str = ""
    vin: str = ""
    calculate_soc: bool = False
    access_token: str = ""
    refresh_token: str = ""
    expires_at: float = 0
    container_id: str = ""
    # Auth-Status für UI (temporär während Device Code Flow)
    auth_user_code: str = ""
    auth_verification_uri: str = ""
    auth_device_code: str = ""
    auth_code_verifier: str = ""
    auth_expires_at: float = 0
    auth_connected: bool = False


@dataclass
class BmwCardataSetup:
    name: str = "BMW CarData"
    type: str = "bmw_cardata"
    official: bool = False
    configuration: BmwCardataConfiguration = None

    def __post_init__(self):
        if self.configuration is None:
            self.configuration = BmwCardataConfiguration()
