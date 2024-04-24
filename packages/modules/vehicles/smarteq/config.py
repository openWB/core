from typing import Optional
import json


class SmartEQConfiguration:
    def __init__(self,
                 user_id: Optional[str] = None,          # show in UI
                 password: Optional[str] = None,         # show in UI
                 pin: Optional[str] = None,              # show in UI
                 vin: Optional[str] = None,              # show in UI
                 useWebSocket: Optional[str] = "False",  # show in UI
                 logFilter: Optional[str] = None,        # show in UI
                 refreshToken: Optional[str] = None,     # DON'T show in UI!
                 opMode: Optional[str] = None            # DON'T show in UI!
                 ):
        self.user_id = user_id
        self.password = password
        self.pin = pin
        self.vin = vin
        self.useWebSocket = useWebSocket
        self.logFilter = logFilter
        self.refreshToken = refreshToken
        self.opMode = opMode


class SmartEQ:
    def __init__(self,
                 name: str = "SmartEQ",
                 type: str = "smarteq",
                 configuration: SmartEQConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.configuration = configuration or SmartEQConfiguration()

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__,
                          sort_keys=True, indent=4)
