from typing import Optional

from modules.vehicles.json.config import JsonSocConfiguration, JsonSocSetup


class PSACCVehicleSocConfiguration(JsonSocConfiguration):
    def __init__(self,
                 psacc_server_or_ip: Optional[str] = None,
                 psacc_port: Optional[int] = None,
                 vehicle_vin: Optional[str] = None) -> None:

        prf = ".energy[0]."
        super().__init__(soc_pattern=prf + "level",
                         range_pattern=prf + "autonomy",
                         timestamp_pattern=prf + "updated_at",
                         timeout=10,
                         calculate_soc=True)

        self.psacc_server_or_ip = psacc_server_or_ip
        self.psacc_port = psacc_port
        self.vehicle_vin = vehicle_vin

    @property
    def url(self) -> str:
        return f'http://{self.psacc_server_or_ip}:{self.psacc_port}/get_vehicleinfo/{self.vehicle_vin}'

    @url.setter
    def url(self, value: Optional[str]):
        pass


class PSACCVehicleSoc(JsonSocSetup):
    def __init__(self,
                 name: str = "PSA Car Controller",
                 type: str = "psacc",
                 configuration: PSACCVehicleSocConfiguration = None) -> None:
        super().__init__(name=name, type=type,
                         configuration=configuration or PSACCVehicleSocConfiguration())
