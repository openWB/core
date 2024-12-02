from typing import Optional

class PSACCVehicleSocConfiguration:
    def __init__(self,
                 psacc_server_or_ip: Optional[str] = None,
                 psacc_port: Optional[int] = None,
                 vehicle_vin: Optional[str] = None) -> None:
        self.psacc_server_or_ip = psacc_server_or_ip
        self.psacc_port = psacc_port
        self.vehicle_vin = vehicle_vin


class PSACCVehicleSoc:
    def __init__(self,
                 name: str = "PSA Car Controller",
                 type: str = "psacc",
                 configuration: PSACCVehicleSocConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.configuration = configuration or PSACCVehicleSocConfiguration()
