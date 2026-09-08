#!/usr/bin/env python3
import logging
from typing import Any, Dict, Optional, TypedDict

from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.simcount import SimCounter
from modules.common.store import get_component_value_store
from modules.devices.fronius.fronius_http_api.config import FroniusBatSetup
from modules.devices.fronius.fronius_http_api.config import FroniusConfiguration
from modules.devices.fronius.fronius_http_api.fronius_api import FroniusWR
from modules.common.utils.peak_filter import PeakFilter
from modules.common.component_type import ComponentType

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
        self.last_mode: Optional[str] = 'Undefined'
        self.bat_api: Optional[FroniusWR] = None

    def update(self, powerflow_response: Dict) -> None:
        meter_id = str(self.component_config.configuration.meter_id)

        # Anders als beim Wechselrichter ist bei Speicher/Zähler ein "keine Antwort" kein normaler
        # Nachtmodus-Zustand, der als 0 W angenommen werden darf -- der Speicher entlädt bzw. der
        # Zähler misst weiterhin, daher hier fehlerhaft werden statt falsche 0-Werte zu melden.
        if isinstance(powerflow_response, Exception):
            raise powerflow_response

        try:
            power = int(powerflow_response["Body"]["Data"]["Site"]["P_Akku"]) * -1
        except TypeError:
            # Wenn WR aus bzw. im Standby (keine Antwort), ersetze leeren Wert durch eine 0.
            power = 0

        try:
            resp_json_id = dict(powerflow_response["Body"]["Data"])
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
        username = self.component_config.configuration.username
        password = self.component_config.configuration.password
        if username is None or password is None:
            log.warning("Fronius Speicher: Keine Batteriesteuerung möglich, da keine Zugangsdaten hinterlegt sind.")
            return

        if self.bat_api is None:
            # Der Verbindungsaufbau (Login, Firmware-Erkennung) passiert erst hier und nicht schon in
            # initialize(), da er echte HTTP-Requests an den Wechselrichter auslöst und ohne Zugangsdaten
            # ohnehin fehlschlagen würde.
            self.bat_api = FroniusWR({
                'address': self.device_config.ip_address,
                'user': username,
                'password': password,
            })
        else:
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
            log.debug(f"Aktive Batteriesteuerung. Batterie wird mit {abs(power_limit)} W "
                      "entladen für den Hausverbrauch")
            self.last_mode = 'discharge'
        elif power_limit > 0:
            self.bat_api.set_mode_force_charge(power_limit)
            log.debug(f"Aktive Batteriesteuerung. Batterie wird mit {power_limit} W geladen")
            self.last_mode = 'charge'

    def power_limit_controllable(self) -> bool:
        # Nur steuerbar, wenn Installateur-Zugangsdaten hinterlegt sind -- sonst würde die aktive
        # Speichersteuerung fälschlich mit diesem Speicher rechnen, obwohl er gar nicht gesteuert wird.
        config = self.component_config.configuration
        return config.username is not None and config.password is not None


component_descriptor = ComponentDescriptor(configuration_factory=FroniusBatSetup)
