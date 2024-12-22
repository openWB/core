from typing import Optional

from modules.vehicles.json.config import JsonSocConfiguration, JsonSocSetup


class PSACCVehicleSocConfiguration(JsonSocConfiguration):
    def __init__(self,
                 psacc_server_or_ip: Optional[str] = None,
                 psacc_port: Optional[int] = None,
                 vehicle_vin: Optional[str] = None) -> None:

        super().__init__(soc_pattern=".energy[0].level",
                         range_pattern=".energy[0].autonomy",
                         timeout=10,
                         calculate_soc=True)

        self.psacc_server_or_ip = psacc_server_or_ip
        self.psacc_port = psacc_port
        self.vehicle_vin = vehicle_vin

    @property
    def url(self):
        return f'http://{self.psacc_server_or_ip}:{self.psacc_port}/get_vehicleinfo/{self.vehicle_vin}'

    @url.setter
    def url(self, value):
        pass


class PSACCVehicleSoc(JsonSocSetup):
    def __init__(self,
                 name: str = "PSA Car Controller",
                 type: str = "psacc",
                 configuration: PSACCVehicleSocConfiguration = None) -> None:
        super().__init__(name=name, type=type,
                         configuration=configuration or PSACCVehicleSocConfiguration())
