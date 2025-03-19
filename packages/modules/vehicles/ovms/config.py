from typing import Optional


class OVMSConfiguration:
    def __init__(self,
                 server_url: Optional[str] = "https://ovms.dexters-web.de:6869",        # show in UI
                 user_id: Optional[str] = None,        # show in UI
                 password: Optional[str] = None,       # show in UI
                 vehicleId: Optional[str] = None,      # show in UI
                 token: Optional[str] = None           # DON'T show in UI!
                 ):
        self.server_url = server_url
        self.user_id = user_id
        self.password = password
        self.vehicleId = vehicleId
        self.token = token


class OVMS:
    def __init__(self,
                 name: str = "OVMS",
                 type: str = "ovms",
                 configuration: OVMSConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.configuration = configuration or OVMSConfiguration()
