#!/usr/bin/env python3
from typing import Dict, Optional
from modules.common import req
from modules.common.component_state import BatState, CounterState, InverterState
from modules.common.simcount import SimCounter


class RestApi1():
    def __init__(self, host: str) -> None:
        self.host = host

    def power_limit_controllable(self) -> bool:
        """
        Checks if the power limit is controllable via the REST API.
        Returns:
            bool: True if controllable, False otherwise.
        """
        return False

    def read(self, device_endpoint: str = 'battery') -> dict:
        """
        Reads data from the Sonnenbatterie REST API.
        Args:
            device_endpoint (str): The device to read data from. Defaults to 'battery'.
        Returns:
            dict: The JSON response from the API.
        """
        return req.get_http_session().get(
            f'http://{self.host}:7979/rest/devices/{device_endpoint}',
            timeout=5).json()

    def update_battery(self, sim_counter: SimCounter) -> BatState:
        """
        Updates the battery state by reading data from the REST API.
        Returns:
            BatState: The updated battery state.
        """
        battery_state = self.read(device_endpoint="battery")
        battery_soc = int(battery_state["M05"])
        battery_export_power = int(battery_state["M34"])
        battery_import_power = int(battery_state["M35"])
        battery_power = battery_import_power - battery_export_power
        imported, exported = sim_counter.sim_count(battery_power)
        return BatState(power=battery_power,
                        soc=battery_soc,
                        imported=imported,
                        exported=exported)


class RestApi2():
    def __init__(self, host: str) -> None:
        self.host = host

    def power_limit_controllable(self) -> bool:
        """
        Checks if the power limit is controllable via the REST API.
        Returns:
            bool: True if controllable, False otherwise.
        """
        return False

    def read_element(self, device: str, element: str) -> str:
        """
        Reads a specific element from the Sonnenbatterie REST API v2.
        Args:
            device (str): The device to read data from.
            element (str): The specific element to read.
        Returns:
            str: The value of the specified element.
        """
        response = req.get_http_session().get(
            f'http://{self.host}:7979/rest/devices/{device}/{element}',
            timeout=5)
        response.encoding = 'utf-8'
        return response.text.strip(" \n\r")

    def update_inverter(self, sim_counter: SimCounter) -> InverterState:
        """
        Updates the inverter state by reading data from the REST API v2.
        Returns:
            InverterState: The updated inverter state.
        """
        pv_power = -int(float(self.read_element(device="battery", element="M03")))
        _, exported = sim_counter.sim_count(pv_power)
        return InverterState(exported=exported,
                             power=pv_power)

    def update_grid_counter(self, sim_counter: SimCounter) -> CounterState:
        """
        Updates the grid counter state by reading data from the REST API v2.
        Returns:
            CounterState: The updated grid counter state.
        """
        grid_import_power = -int(float(self.read_element(device="battery", element="M39")))
        grid_export_power = -int(float(self.read_element(device="battery", element="M38")))
        grid_power = grid_import_power - grid_export_power
        imported, exported = sim_counter.sim_count(grid_power)
        return CounterState(power=grid_power,
                            imported=imported,
                            exported=exported)

    def update_battery(self, sim_counter: SimCounter) -> BatState:
        """
        Updates the battery state by reading data from the REST API v2.
        Returns:
            BatState: The updated battery state.
        """
        battery_soc = int(float(self.read_element(device="battery", element="M05")))
        battery_export_power = int(float(self.read_element(device="battery", element="M01")))
        battery_import_power = int(float(self.read_element(device="battery", element="M02")))
        battery_power = battery_import_power - battery_export_power
        imported, exported = sim_counter.sim_count(battery_power)
        return BatState(power=battery_power,
                        soc=battery_soc,
                        imported=imported,
                        exported=exported)


class JsonApi():
    def __init__(self, host: str, api_version: str = "v1", auth_token: Optional[str] = None) -> None:
        self.host = host
        self.api_version = api_version
        self.auth_token = auth_token
        if self.api_version == "v2" and self.auth_token is None:
            raise ValueError("API v2 requires an auth_token.")
        self.headers = {"auth-token": auth_token} if api_version == "v2" else {}

    def power_limit_controllable(self) -> bool:
        """
        Checks if the power limit is controllable via the JSON API.
        Returns:
            bool: True if controllable, False otherwise.
        """
        return self.api_version == "v2" and self.auth_token is not None

    def read(self, endpoint: str = "status") -> Dict:
        """
        Reads data from the Sonnenbatterie JSON API.

        Args:
            endpoint (str): The endpoint to fetch data from. Defaults to "status".

        Returns:
            Dict: The JSON response from the API as a dictionary.
        """
        return req.get_http_session().get(
            f"http://{self.host}/api/{self.api_version}/{endpoint}",
            timeout=5,
            headers=self.headers
        ).json()

    def update_inverter(self, sim_counter: SimCounter) -> InverterState:
        """
        Updates the inverter state by reading data from the JSON API.
        Returns:
            InverterState: The updated inverter state.
        example data:
        {
            "Apparent_output": 225,
            "BackupBuffer": "0",
            "BatteryCharging": false,
            "BatteryDischarging": false,
            "Consumption_Avg": 2114,
            "Consumption_W": 2101,
            "Fac": 49.97200393676758,
            "FlowConsumptionBattery": false,
            "FlowConsumptionGrid": true,
            "FlowConsumptionProduction": false,
            "FlowGridBattery": false,
            "FlowProductionBattery": false,
            "FlowProductionGrid": false,
            "GridFeedIn_W": -2106,
            "IsSystemInstalled": 1,
            "OperatingMode": "2",
            "Pac_total_W": -5,
            "Production_W": 0,
            "RSOC": 6,
            "RemainingCapacity_Wh": 2377,
            "Sac1": 75,
            "Sac2": 75,
            "Sac3": 75,
            "SystemStatus": "OnGrid",
            "Timestamp": "2021-12-13 07:54:48",
            "USOC": 0,
            "Uac": 231,
            "Ubat": 48,
            "dischargeNotAllowed": true,
            "generator_autostart": false,
            "NVM_REINIT_STATUS": 0
        }
        """
        inverter_state = self.read(endpoint="status")
        pv_power = -inverter_state["Production_W"]
        _, exported = sim_counter.sim_count(pv_power)
        return InverterState(exported=exported,
                             power=pv_power)

    def update_grid_counter(self, sim_counter: SimCounter) -> CounterState:
        """
        Updates the grid counter state by reading data from the JSON API.
        Returns:
            CounterState: The updated grid counter state.
        example data:
        {
            "Apparent_output": 225,
            "BackupBuffer": "0",
            "BatteryCharging": false,
            "BatteryDischarging": false,
            "Consumption_Avg": 2114,
            "Consumption_W": 2101,
            "Fac": 49.97200393676758,
            "FlowConsumptionBattery": false,
            "FlowConsumptionGrid": true,
            "FlowConsumptionProduction": false,
            "FlowGridBattery": false,
            "FlowProductionBattery": false,
            "FlowProductionGrid": false,
            "GridFeedIn_W": -2106,
            "IsSystemInstalled": 1,
            "OperatingMode": "2",
            "Pac_total_W": -5,
            "Production_W": 0,
            "RSOC": 6,
            "RemainingCapacity_Wh": 2377,
            "Sac1": 75,
            "Sac2": 75,
            "Sac3": 75,
            "SystemStatus": "OnGrid",
            "Timestamp": "2021-12-13 07:54:48",
            "USOC": 0,
            "Uac": 231,
            "Ubat": 48,
            "dischargeNotAllowed": true,
            "generator_autostart": false,
            "NVM_REINIT_STATUS": 0
        }
        """
        counter_state = self.read(endpoint="status")
        grid_power = -counter_state["GridFeedIn_W"]
        grid_voltage = counter_state["Uac"]
        grid_frequency = counter_state["Fac"]
        imported, exported = sim_counter.sim_count(grid_power)
        return CounterState(power=grid_power,
                            voltages=[grid_voltage]*3,
                            frequency=grid_frequency,
                            imported=imported,
                            exported=exported)

    def update_consumption_counter(self) -> CounterState:
        """
        Updates the consumption counter state by reading data from the JSON API.
        Returns:
            CounterState: The updated consumption counter state.
        example data:
        [
            {
                "a_l1": 0,
                "a_l2": 0,
                "a_l3": 0,
                "channel": 1,
                "deviceid": 4,
                "direction": "production",
                "error": -1,
                "kwh_exported": 0,
                "kwh_imported": 0,
                "v_l1_l2": 0,
                "v_l1_n": 0,
                "v_l2_l3": 0,
                "v_l2_n": 0,
                "v_l3_l1": 0,
                "v_l3_n": 0,
                "va_total": 0,
                "var_total": 0,
                "w_l1": 0,
                "w_l2": 0,
                "w_l3": 0,
                "w_total": 0
            },
            {
                "a_l1": 0,
                "a_l2": 0,
                "a_l3": 0,
                "channel": 2,
                "deviceid": 4,
                "direction": "consumption",
                "error": -1,
                "kwh_exported": 0,
                "kwh_imported": 0,
                "v_l1_l2": 0,
                "v_l1_n": 0,
                "v_l2_l3": 0,
                "v_l2_n": 0,
                "v_l3_l1": 0,
                "v_l3_n": 0,
                "va_total": 0,
                "var_total": 0,
                "w_l1": 0,
                "w_l2": 0,
                "w_l3": 0,
                "w_total": 0
            }
        ]
        """
        result = self.read(endpoint="powermeter")
        for channel in result:
            if channel["direction"] == "consumption":
                return CounterState(power=channel["w_total"],
                                    powers=[channel[f"w_l{phase}"] for phase in range(1, 4)],
                                    currents=[channel[f"a_l{phase}"] for phase in range(1, 4)],
                                    voltages=[channel[f"v_l{phase}_n"] for phase in range(1, 4)],
                                    imported=channel["kwh_imported"],
                                    exported=channel["kwh_exported"])
        raise ValueError("No consumption data found in the response.")

    def update_battery(self, sim_counter: SimCounter) -> BatState:
        """
        Updates the battery state by reading data from the JSON API.
        Returns:
            InverterState: The updated battery state.
        example data:
        {
            "Apparent_output": 225,
            "BackupBuffer": "0",
            "BatteryCharging": false,
            "BatteryDischarging": false,
            "Consumption_Avg": 2114,
            "Consumption_W": 2101,
            "Fac": 49.97200393676758,
            "FlowConsumptionBattery": false,
            "FlowConsumptionGrid": true,
            "FlowConsumptionProduction": false,
            "FlowGridBattery": false,
            "FlowProductionBattery": false,
            "FlowProductionGrid": false,
            "GridFeedIn_W": -2106,
            "IsSystemInstalled": 1,
            "OperatingMode": "2",
            "Pac_total_W": -5,
            "Production_W": 0,
            "RSOC": 6,
            "RemainingCapacity_Wh": 2377,
            "Sac1": 75,
            "Sac2": 75,
            "Sac3": 75,
            "SystemStatus": "OnGrid",
            "Timestamp": "2021-12-13 07:54:48",
            "USOC": 0,
            "Uac": 231,
            "Ubat": 48,
            "dischargeNotAllowed": true,
            "generator_autostart": false
        }
        """
        battery_state = self.read(endpoint="status")
        battery_power = -battery_state["Pac_total_W"]
        battery_soc = battery_state["USOC"]
        imported, exported = sim_counter.sim_count(battery_power)
        return BatState(power=battery_power,
                        soc=battery_soc,
                        imported=imported,
                        exported=exported)

    def get_configurations(self) -> Dict:
        if self.api_version != "v2":
            raise ValueError("Diese Methode erfordert die JSON API v2!")
        return self.read(endpoint="configurations")

    def set_configurations(self, configuration: Dict) -> None:
        if self.api_version != "v2":
            raise ValueError("Diese Methode erfordert die JSON API v2!")
        req.get_http_session().put(f"http://{self.host}/api/v2/configurations",
                                   json=configuration,
                                   headers={"Auth-Token": self.auth_token})

    def update_set_point(self, power_limit: int) -> None:
        if self.api_version != "v2":
            raise ValueError("Diese Methode erfordert die JSON API v2!")
        command = "charge"
        if power_limit < 0:
            command = "discharge"
            power_limit = -power_limit
        req.get_http_session().post(f"http://{self.host}/api/v2/setpoint/{command}/{power_limit}",
                                    headers={"Auth-Token": self.auth_token,
                                             "Content-Type": "application/json"})

    def set_power_limit(self, power_limit: Optional[int]) -> None:
        if self.power_limit_controllable() is False:
            raise ValueError("Leistungsvorgabe wird nur für 'JSON-API v2' unterstützt!")
        operating_mode = self.get_configurations()["EM_OperatingMode"]
        if power_limit is None:
            # Keine Leistungsvorgabe, Betriebsmodus "Eigenverbrauch" aktivieren
            if operating_mode == "1":
                self.set_configurations({"EM_OperatingMode": "2"})
        else:
            # Leistungsvorgabe, Betriebsmodus "Manuell" aktivieren
            if operating_mode == "2":
                self.set_configurations({"EM_OperatingMode": "1"})
            self.update_set_point(power_limit)
