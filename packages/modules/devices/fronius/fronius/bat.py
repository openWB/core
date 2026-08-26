#!/usr/bin/env python3
from typing import Any, TypedDict, Optional
import logging

from modules.common import req
from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.simcount import SimCounter
from modules.common.store import get_component_value_store
from modules.devices.fronius.fronius.config import FroniusBatSetup
from modules.devices.fronius.fronius.config import FroniusConfiguration
from modules.common.utils.peak_filter import PeakFilter
from modules.common.component_type import ComponentType
from modules.devices.fronius.fronius.bat_api.bat_api import FroniusWR

log = logging.getLogger(__name__)

class KwargsDict(TypedDict):
    device_config: FroniusConfiguration
    device_id: int


class FroniusBat(AbstractBat):
    def __init__(self, component_config: FroniusBatSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.device_config: FroniusConfiguration = self.kwargs['device_config']
        self.__device_id: int = self.kwargs['device_id']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, self.component_config.type)
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.peak_filter = PeakFilter(ComponentType.BAT, self.component_config.id, self.fault_state)
        self.last_mode = 'Undefined'
        self.bat_api = None
    def update(self) -> None:
        meter_id = str(self.component_config.configuration.meter_id)

        resp_json = req.get_http_session().get(
            'http://' + self.device_config.ip_address + '/solar_api/v1/GetPowerFlowRealtimeData.fcgi',
            params=(('Scope', 'System'),),
            timeout=5).json()
        try:
            power = int(resp_json["Body"]["Data"]["Site"]["P_Akku"]) * -1
        except TypeError:
            # Wenn WR aus bzw. im Standby (keine Antwort), ersetze leeren Wert durch eine 0.
            power = 0

        try:
            resp_json_id = dict(resp_json["Body"]["Data"])
            if "Inverters" in resp_json_id:
                soc = float(resp_json_id["Inverters"]["1"]["SOC"])
            else:
                soc = float(resp_json_id.get(meter_id)["Controller"]["StateOfCharge_Relative"])
        except TypeError:
            # Wenn WR aus bzw. im Standby (keine Antwort), ersetze leeren Wert durch eine 0.
            soc = 0

        self.peak_filter.check_values(power)
        imported, exported = self.sim_counter.sim_count(power)
        bat_state = BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )
        self.store.set(bat_state)

    def set_power_limit(self, power_limit: Optional[int]) -> None:
        if self.component_config.configuration.username is None:
            username = "technician"
        else:
            username = self.component_config.configuration.username
        if self.component_config.configuration.password is None:
            password = "gain-^LwP3T4"
        else:
            password = self.component_config.configuration.password
        if self.bat_api is None:
            config = {
                'address': self.device_config.ip_address,
                'user': username,
                'password': password
            }
            self.bat_api = FroniusWR(config)
        if username is not None and password is not None:
            self.bat_api.set_config(self.device_config.ip_address, username, password)

            log.debug(f'last_mode: {self.last_mode}')

            if power_limit is None:
                log.debug("Keine Batteriesteuerung, Selbstregelung durch Wechselrichter")
                if self.last_mode is not None:
                    self.bat_api.set_mode_self_regulation()
                    self.last_mode = None
            elif power_limit == 0:
                log.debug("Aktive Batteriesteuerung. Batterie wird auf Stop gesetzt und nicht entladen")
                if self.last_mode != 'stop':
                    self.bat_api.set_mode_avoid_discharge()
                    self.last_mode = 'stop'
            elif power_limit < 0:
                self.bat_api.set_mode_force_discharge(abs(power_limit))
                log.debug(f"Aktive Batteriesteuerung. Batterie wird mit {abs(power_limit)} W entladen für den Hausverbrauch")
                self.last_mode = 'discharge'
            elif power_limit > 0:
                self.bat_api.set_mode_force_charge(power_limit)
                log.debug(f"Aktive Batteriesteuerung. Batterie wird mit {power_limit} W geladen")
                self.last_mode = 'charge'
        else:
            log.warning("Fronius Speicher: Keine Batteriesteuerung möglich, da keine Zugangsdaten hinterlegt sind.")


    def power_limit_controllable(self) -> bool:
        return True


component_descriptor = ComponentDescriptor(configuration_factory=FroniusBatSetup)
