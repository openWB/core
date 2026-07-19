from typing import Optional


class VWEUDAConfiguration:
    def __init__(self,
                 user_id: Optional[str] = None,        # show in UI
                 password: Optional[str] = None,       # show in UI
                 vin: Optional[str] = None,            # show in UI
                 calculate_soc: bool = False           # show in UI
                 ):
        self.user_id = user_id
        self.password = password
        self.vin = vin
        self.calculate_soc = calculate_soc


class VWEUDA:
    def __init__(self,
                 name: str = "VWEUDA",
                 type: str = "vweuda",
                 official: bool = False,
                 configuration: VWEUDAConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.official = official
        self.configuration = configuration or VWEUDAConfiguration()
