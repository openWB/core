#!/usr/bin/env python3
import logging
from typing import Dict, Optional, Union

from dataclass_utils import dataclass_from_dict
from modules.common import req
from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.simcount import SimCounter
from modules.common.store import get_bat_value_store
from modules.devices.sonnen.sonnenbatterie.config import SonnenbatterieBatSetup

log = logging.getLogger(__name__)


class SonnenbatterieBat(AbstractBat):
    def __init__(self,
                 device_id: int,
                 device_address: str,
                 device_variant: int,
                 api_v2_token: Optional[str],
                 component_config: Union[Dict, SonnenbatterieBatSetup]) -> None:
        self.__device_id = device_id
        self.__device_address = device_address
        self.__device_variant = device_variant
        self.__api_v2_token = api_v2_token
        self.component_config = dataclass_from_dict(SonnenbatterieBatSetup, component_config)
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="speicher")
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def __read_variant_0(self):
        return req.get_http_session().get('http://' + self.__device_address + ':7979/rest/devices/battery',
                                          timeout=5).json()

    def __update_variant_0(self) -> BatState:
        # Auslesen einer Sonnenbatterie Eco 4 über die integrierte JSON-API des Batteriesystems
        battery_state = self.__read_variant_0()
        battery_soc = int(battery_state["M05"])
        battery_export_power = int(battery_state["M34"])
        battery_import_power = int(battery_state["M35"])
        battery_power = battery_import_power - battery_export_power
        return BatState(
            power=battery_power,
            soc=battery_soc
        )

    def __read_variant_1(self, api: str = "v1", target: str = "status") -> Dict:
        return req.get_http_session().get(
            f"http://{self.__device_address}/api/{api}/{target}",
            timeout=5,
            headers={"Auth-Token": self.__api_v2_token} if api == "v2" else None
        ).json()

    def __update_variant_1(self, api: str = "v1") -> BatState:
        # Auslesen einer Sonnenbatterie 8 oder 10 über die integrierte JSON-API v1/v2 des Batteriesystems
        '''
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
        '''
        battery_state = self.__read_variant_1(api)
        battery_power = -battery_state["Pac_total_W"]
        log.debug('Speicher Leistung: ' + str(battery_power))
        battery_soc = battery_state["USOC"]
        log.debug('Speicher SoC: ' + str(battery_soc))
        imported, exported = self.sim_counter.sim_count(battery_power)
        return BatState(
            power=battery_power,
            soc=battery_soc,
            imported=imported,
            exported=exported
        )

    def __get_json_api_v2_configurations(self) -> Dict:
        if self.__device_variant != 3:
            raise ValueError("JSON API v2 wird nur für Variante 3 unterstützt!")
        return self.__read_variant_1("v2", "configurations")

    def __set_json_api_v2_configurations(self, configuration: Dict) -> None:
        if self.__device_variant != 3:
            raise ValueError("JSON API v2 wird nur für Variante 3 unterstützt!")
        req.get_http_session().put(
            f"http://{self.__device_address}/api/v2/configurations",
            json=configuration,
            headers={"Auth-Token": self.__api_v2_token}
        )

    def __set_json_api_v2_setpoint(self, power_limit: int) -> None:
        if self.__device_variant != 3:
            raise ValueError("JSON API v2 wird nur für Variante 3 unterstützt!")
        command = "charge"
        if power_limit < 0:
            command = "discharge"
            power_limit = -power_limit
        req.get_http_session().post(
            f"http://{self.__device_address}/api/v2/setpoint/{command}/{power_limit}",
            headers={"Auth-Token": self.__api_v2_token, "Content-Type": "application/json"}
        )

    def __read_variant_2_element(self, element: str) -> str:
        response = req.get_http_session().get(
            'http://' + self.__device_address + ':7979/rest/devices/battery/' + element,
            timeout=5)
        response.encoding = 'utf-8'
        return response.text.strip(" \n\r")

    def __update_variant_2(self) -> BatState:
        # Auslesen einer Sonnenbatterie Eco 6 über die integrierte REST-API des Batteriesystems
        battery_soc = int(float(self.__read_variant_2_element("M05")))
        battery_export_power = int(float(self.__read_variant_2_element("M01")))
        battery_import_power = int(float(self.__read_variant_2_element("M02")))
        battery_power = battery_import_power - battery_export_power
        return BatState(
            power=battery_power,
            soc=battery_soc
        )

    def update(self) -> None:
        log.debug("Variante: " + str(self.__device_variant))
        if self.__device_variant == 0:
            state = self.__update_variant_0()
        elif self.__device_variant == 1:
            state = self.__update_variant_1()
        elif self.__device_variant == 2:
            state = self.__update_variant_2()
        elif self.__device_variant == 3:
            state = self.__update_variant_1("v2")
        else:
            raise ValueError("Unbekannte Variante: " + str(self.__device_variant))
        self.store.set(state)

    def set_power_limit(self, power_limit: Optional[int]) -> None:
        if self.__device_variant != 3:
            raise ValueError("Leistungsvorgabe wird nur für Variante 'JSON-API v2' unterstützt!")
        operating_mode = self.__get_json_api_v2_configurations()["EM_OperatingMode"]
        log.debug(f"Betriebsmodus: aktuell: {operating_mode}")
        if power_limit is None:
            # Keine Leistungsvorgabe, Betriebsmodus "Eigenverbrauch" aktivieren
            if operating_mode == "1":
                log.debug("Keine Leistungsvorgabe, aktiviere normale Steuerung durch den Speicher")
                self.__set_json_api_v2_configurations({"EM_OperatingMode": "2"})
        else:
            # Leistungsvorgabe, Betriebsmodus "Manuell" aktivieren
            if operating_mode == "2":
                log.debug(f"Leistungsvorgabe: {power_limit}, aktiviere manuelle Steuerung durch openWB")
                self.__set_json_api_v2_configurations({"EM_OperatingMode": "1"})
            log.debug(f"Setze Leistungsvorgabe auf: {power_limit}")
            self.__set_json_api_v2_setpoint(power_limit)

    def power_limit_controllable(self) -> bool:
        # Leistungsvorgabe ist nur für Variante 3 (JSON-API v2) möglich
        return self.__device_variant == 3


component_descriptor = ComponentDescriptor(configuration_factory=SonnenbatterieBatSetup)
