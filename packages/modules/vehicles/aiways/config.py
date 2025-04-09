from typing import Optional

"""
The attributes for configuration can be retrieved with this guide:
https://community.home-assistant.io/t/read-aiways-u5-state-of-charge/466441/5
"""


class AiwaysVehicleSocConfiguration:
    def __init__(self, user_id: Optional[str] = None, vin: Optional[str] = None, device_id: Optional[str] = None,
                 register_id: Optional[str] = None, token: Optional[str] = None,
                 condition_url: Optional[str] = "https://coiapp-api-eu.ai-ways.com:10443/app/vc/getCondition") -> None:
        self.user_id = user_id
        self.vin = vin
        self.device_id = device_id
        self.register_id = register_id
        self.token = token
        self.condition_url = condition_url


class AiwaysVehicleSoc:
    def __init__(self,
                 name: str = "Aiways",
                 type: str = "aiways",
                 configuration: AiwaysVehicleSocConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.configuration = configuration or AiwaysVehicleSocConfiguration()
