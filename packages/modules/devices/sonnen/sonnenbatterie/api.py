#!/usr/bin/env python3
import logging
from enum import Enum
from typing import Dict, List, Optional, TypedDict, Union
from modules.common import req
from modules.common.component_state import BatState, CounterState, InverterState
from modules.common.simcount import SimCounter


log = logging.getLogger(__name__)


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

    def __read(self, device_endpoint: str = 'battery') -> dict:
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
        battery_state = self.__read(device_endpoint="battery")
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

    def __read_element(self, device: str, element: str) -> str:
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
        pv_power = -int(float(self.__read_element(device="battery", element="M03")))
        _, exported = sim_counter.sim_count(pv_power)
        return InverterState(exported=exported,
                             power=pv_power)

    def update_grid_counter(self, sim_counter: SimCounter) -> CounterState:
        """
        Updates the grid counter state by reading data from the REST API v2.
        Returns:
            CounterState: The updated grid counter state.
        """
        grid_import_power = -int(float(self.__read_element(device="battery", element="M39")))
        grid_export_power = -int(float(self.__read_element(device="battery", element="M38")))
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
        battery_soc = int(float(self.__read_element(device="battery", element="M05")))
        battery_export_power = int(float(self.__read_element(device="battery", element="M01")))
        battery_import_power = int(float(self.__read_element(device="battery", element="M02")))
        battery_power = battery_import_power - battery_export_power
        imported, exported = sim_counter.sim_count(battery_power)
        return BatState(power=battery_power,
                        soc=battery_soc,
                        imported=imported,
                        exported=exported)


class JsonApiVersion(Enum):
    V1 = "v1"
    V2 = "v2"


class JsonApi():
    class OperatingMode(Enum):
        MANUAL = "1"
        SELF_CONSUMPTION = "2"
        TIME_OF_USE = "10"

    class PowerMeterDirection(Enum):
        PRODUCTION = "production"
        CONSUMPTION = "consumption"

    class StatusDict(TypedDict):
        Apparent_output: int
        BackupBuffer: str
        BatteryCharging: bool
        BatteryDischarging: bool
        Consumption_Avg: int
        Consumption_W: int
        Fac: float
        FlowConsumptionBattery: bool
        FlowConsumptionGrid: bool
        FlowConsumptionProduction: bool
        FlowGridBattery: bool
        FlowProductionBattery: bool
        FlowProductionGrid: bool
        GridFeedIn_W: int
        IsSystemInstalled: int
        OperatingMode: str
        Pac_total_W: int
        Production_W: int
        RSOC: int
        RemainingCapacity_Wh: int
        Sac1: int
        Sac2: int
        Sac3: int
        SystemStatus: str
        Timestamp: str
        USOC: int
        Uac: float
        Ubat: float

    class ChannelDict(TypedDict):
        a_l1: int
        a_l2: int
        a_l3: int
        channel: int
        deviceid: int
        direction: str
        error: int
        kwh_exported: float
        kwh_imported: float
        v_l1_l2: float
        v_l1_n: float
        v_l2_l3: float
        v_l2_n: float
        v_l3_l1: float
        v_l3_n: float
        va_total: float
        var_total: float
        w_l1: float
        w_l2: float
        w_l3: float
        w_total: float

    default_operating_mode: Optional[OperatingMode] = None

    def __init__(self,
                 host: str,
                 api_version: JsonApiVersion = JsonApiVersion.V1,
                 auth_token: Optional[str] = None) -> None:
        self.host = host
        self.api_version = api_version
        self.auth_token = auth_token
        if self.api_version == JsonApiVersion.V2 and self.auth_token is None:
            raise ValueError("API v2 requires an auth_token.")
        self.headers = {"auth-token": auth_token} if api_version == JsonApiVersion.V2 else {}

    def __del__(self) -> None:
        """
        Destructor to clean up the object.
        """
        # restore normal operating mode
        if self.api_version == JsonApiVersion.V2:
            self.set_power_limit(None)

    def __read(self, endpoint: str = "status") -> Dict:
        """
        Reads data from the Sonnenbatterie JSON API.
        Args:
            endpoint (str): The endpoint to fetch data from. Defaults to "status".
        Returns:
            Dict: The JSON response from the API as a dictionary.
        """
        return req.get_http_session().get(
            f"http://{self.host}/api/{self.api_version.value}/{endpoint}",
            timeout=5,
            headers=self.headers
        ).json()

    def __read_status(self) -> StatusDict:
        """
        Reads the status data from the JSON API.
        Returns:
            StatusDict: The status data as a dictionary.
        """
        return self.__read(endpoint="status")

    def __read_power_meter(self, direction: Optional[PowerMeterDirection] = None) -> List[ChannelDict]:
        """
        Reads the power meter data from the JSON API.
        Args:
            direction (Optional[PowerMeterDirection]): The direction of the power meter data.
                If None, all data is returned. Defaults to None.
        Returns:
            List[ChannelDict]: The power meter data as a list of dictionaries.
        """
        data = self.__read(endpoint="powermeter")
        if direction is not None:
            data = [item for item in data if item["direction"] == direction.value]
            if len(data) == 0:
                raise ValueError(f"No data found for direction: {direction.value}")
        return data

    def __state_from_channel(self, channel: ChannelDict) -> Union[CounterState, InverterState]:
        """
        Converts a channel dictionary to a CounterState or InverterState object based on channel["direction"].
        If the direction is "consumption", it returns a CounterState object.
        If the direction is "production", it returns an InverterState object.
        If the direction is neither, it raises a ValueError.
        Args:
            channel (ChannelDict): The channel data as a dictionary.
        Returns:
            CounterState|InverterState: The converted State object.
        Raises:
            ValueError: If the direction is neither "consumption" nor "production".
        """
        if channel["direction"] == self.PowerMeterDirection.CONSUMPTION.value:
            powers = [channel[f"w_l{phase}"] for phase in range(1, 4)]
            currents = [channel[f"a_l{phase}"] for phase in range(1, 4)]
            voltages = [channel[f"v_l{phase}_n"] for phase in range(1, 4)]
            power_factors = [
                powers[phase] / (voltages[phase] * currents[phase])
                if voltages[phase] and currents[phase] else None
                for phase in range(0, 3)
            ]
            return CounterState(power=channel["w_total"],
                                powers=powers,
                                currents=currents,
                                voltages=voltages,
                                power_factors=power_factors,
                                imported=channel["kwh_imported"] * 1000,
                                exported=channel["kwh_exported"] * 1000)
        elif channel["direction"] == self.PowerMeterDirection.PRODUCTION.value:
            return InverterState(power=-channel["w_total"],
                                 # powers=[-channel[f"w_l{phase}"] for phase in range(1, 4)],
                                 currents=[-channel[f"a_l{phase}"] for phase in range(1, 4)],
                                 # voltages=[channel[f"v_l{phase}_n"] for phase in range(1, 4)],
                                 # imported=channel["kwh_exported"] * 1000,
                                 exported=channel["kwh_imported"] * 1000)
        else:
            raise ValueError(f"Unknown direction: {channel['direction']}")

    def __get_configurations(self) -> Dict:
        """
        Reads the configurations from the JSON API.
        Returns:
            Dict: The configurations as a dictionary.
        Raises:
            ValueError: If the API version is not v2.
        """
        if self.api_version != JsonApiVersion.V2:
            raise ValueError("Diese Methode erfordert die JSON API v2!")
        return self.__read(endpoint="configurations")

    def __set_configurations(self, configuration: Dict) -> None:
        """
        Sets the configurations for the battery system.
        Args:
            configuration (Dict): The configurations to set.
        Raises:
            ValueError: If the API version is not v2.
        """
        if self.api_version != JsonApiVersion.V2:
            raise ValueError("Diese Methode erfordert die JSON API v2!")
        req.get_http_session().put(f"http://{self.host}/api/v2/configurations",
                                   json=configuration,
                                   headers={"Auth-Token": self.auth_token})

    def __update_set_point(self, power_limit: int) -> None:
        """
        Updates the set point for the battery system.
        Args:
            power_limit (int): The desired power limit in watts. A positive value indicates
                               charging, while a negative value indicates discharging.
        Raises:
            ValueError: If the API version is not v2.
        """
        if self.api_version != JsonApiVersion.V2:
            raise ValueError("Diese Methode erfordert die JSON API v2!")
        command = "charge"
        if power_limit < 0:
            command = "discharge"
            power_limit = -power_limit
        req.get_http_session().post(f"http://{self.host}/api/v2/setpoint/{command}/{power_limit}",
                                    headers={"Auth-Token": self.auth_token,
                                             "Content-Type": "application/json"})

    def power_limit_controllable(self) -> bool:
        """
        Checks if the power limit is controllable via the JSON API.
        Returns:
            bool: True if controllable, False otherwise.
        """
        return self.api_version == JsonApiVersion.V2 and self.auth_token is not None

    def update_battery(self, sim_counter: SimCounter) -> BatState:
        """
        Updates the battery state by reading data from the JSON API.
        Returns:
            InverterState: The updated battery state.
        """
        battery_state = self.__read_status()
        battery_power = -battery_state["Pac_total_W"]
        battery_soc = battery_state["USOC"]
        # try to calculate the individual line currents as no data is provided by the API
        # we assume that the voltage is the same for all three phases
        # this is not correct, but we have no other way to get the currents
        # the current is calculated as apparent power / voltage
        battery_ac_voltage = battery_state["Uac"]
        currents = [float(battery_state[f"Sac{phase}"]) / battery_ac_voltage
                    if battery_state[f"Sac{phase}"] else None
                    for phase in range(1, 4)]
        imported, exported = sim_counter.sim_count(battery_power)
        return BatState(power=battery_power,
                        currents=currents if None not in currents else None,
                        soc=battery_soc,
                        imported=imported,
                        exported=exported)

    def update_grid_counter(self, sim_counter: SimCounter) -> CounterState:
        """
        Updates the grid counter state by reading data from the JSON API.
        Returns:
            CounterState: The updated grid counter state.
        """
        counter_state = self.__read_status()
        grid_power = -counter_state["GridFeedIn_W"]
        grid_voltage = counter_state["Uac"]
        grid_frequency = counter_state["Fac"]
        imported, exported = sim_counter.sim_count(grid_power)
        return CounterState(power=grid_power,
                            voltages=[grid_voltage]*3,
                            frequency=grid_frequency,
                            imported=imported,
                            exported=exported)

    def update_inverter(self, sim_counter: SimCounter) -> InverterState:
        """
        Updates the inverter state by reading data from the JSON API.
        Returns:
            InverterState: The updated inverter state.
        """
        if self.api_version == JsonApiVersion.V1:
            inverter_state = self.__read_status()
            pv_power = -inverter_state["Production_W"]
            _, exported = sim_counter.sim_count(pv_power)
            return InverterState(exported=exported,
                                 power=pv_power)
        else:
            inverter_state = self.__state_from_channel(
                self.__read_power_meter(direction=self.PowerMeterDirection.PRODUCTION)[0])
            # meter value is updated way too slow, so we use a sim counter to get the exported energy
            _, inverter_state.exported = sim_counter.sim_count(inverter_state.power)
            return inverter_state

    def update_consumption_counter(self, sim_counter: SimCounter) -> CounterState:
        """
        Updates the consumption counter state by reading data from the JSON API.
        Returns:
            CounterState: The updated consumption counter state.
        """
        counter_state = self.__state_from_channel(
            self.__read_power_meter(direction=self.PowerMeterDirection.CONSUMPTION)[0])
        # meter value is updated way too slow, so we use a sim counter to get the im-/exported energy
        counter_state.imported, counter_state.exported = sim_counter.sim_count(counter_state.power)
        return counter_state

    def set_power_limit(self, power_limit: Optional[int]) -> None:
        """
        Sets the power limit for the battery system.

        This method adjusts the operating mode and power limit of the battery system
        based on the provided `power_limit` value. If `power_limit` is None, the method
        switches the operating mode to "Self Consumption". Otherwise, it switches the
        operating mode to "Manual" and sets the specified power limit.

        Args:
            power_limit (Optional[int]): The desired power limit in watts. A positive value
                                         indicates charging, while a negative value indicates
                                         discharging. If None, the power limit is removed.

        Raises:
            ValueError: If the power limit control is not supported or the API version is not v2.
            KeyError: If the required key 'EM_OperatingMode' is missing in the API response.
        """
        if self.power_limit_controllable() is False:
            raise ValueError("Leistungsvorgabe wird nur für 'JSON-API v2' unterstützt!")
        configurations = self.__get_configurations()
        if "EM_OperatingMode" not in configurations:
            raise KeyError("The key 'EM_OperatingMode' is missing in the API response.")
        if self.default_operating_mode is None:
            # Store the default operating mode for later restoration
            self.default_operating_mode = self.OperatingMode(configurations["EM_OperatingMode"])
            log.debug(f"default_operating_mode set to: {self.default_operating_mode}")

        operating_mode = self.OperatingMode(configurations["EM_OperatingMode"])
        if power_limit is None:
            # No specific power limit is set, activating default mode to allow the system to optimize energy usage by it
            # self.
            if operating_mode == self.OperatingMode.MANUAL and self.default_operating_mode != self.OperatingMode.MANUAL:
                self.__set_configurations({"EM_OperatingMode": self.default_operating_mode.value})
        else:
            # Activate "Manual" operating mode to allow direct control of the power limit
            # when a specific `power_limit` value is provided.
            if operating_mode != self.OperatingMode.MANUAL:
                self.__set_configurations({"EM_OperatingMode": self.OperatingMode.MANUAL.value})
            self.__update_set_point(power_limit)
