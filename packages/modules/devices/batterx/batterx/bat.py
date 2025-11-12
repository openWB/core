#!/usr/bin/env python3
import logging
from typing import Dict, TypedDict, Any, Optional

from modules.devices.batterx.batterx.config import BatterXBatSetup
from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.simcount import SimCounter
from modules.common.store import get_bat_value_store
from modules.common import req

log = logging.getLogger(__name__)


class KwargsDict(TypedDict):
    device_id: int
    ip_address: str


class BatterXBat(AbstractBat):
    def __init__(self, component_config: BatterXBatSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.__ip_address: str = self.kwargs['ip_address']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="speicher")
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.last_mode = 'Undefined'

    def update(self, resp: Dict) -> None:
        power = resp["1121"]["1"]
        soc = resp["1074"]["1"]
        imported, exported = self.sim_counter.sim_count(power)
        bat_state = BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )
        self.store.set(bat_state)

    def set_power_limit(self, power_limit: Optional[int]) -> None:
        log.debug(f'last_mode: {self.last_mode}')

        if power_limit is None:
            # Kein Powerlimit gefordert, externe Steuerung deaktivieren
            log.debug("Keine Batteriesteuerung gefordert, deaktiviere externe Steuerung.")
            if self.last_mode is not None:
                # Battery Charge AC - OFF
                req.get_http_session().get(
                    f"http://{self.__ip_address}/api.php?set=command&type=20738&text1=3&text2=0",
                    timeout=5
                )
                # Battery Discharging - ON
                req.get_http_session().get(
                    f"http://{self.__ip_address}/api.php?set=command&type=20738&text1=4&text2=1",
                    timeout=5
                )
                self.last_mode = None
        elif power_limit <= 0:
            # BatterX kann Entladung nur komplett sperren
            log.debug("Aktive Batteriesteuerung vorhanden. Setze externe Steuerung.")
            if self.last_mode != 'stop':
                # Battery Charge AC - OFF
                req.get_http_session().get(
                    f"http://{self.__ip_address}/api.php?set=command&type=20738&text1=3&text2=0",
                    timeout=5
                )
                # Battery Discharging - OFF
                req.get_http_session().get(
                    f"http://{self.__ip_address}/api.php?set=command&type=20738&text1=4&text2=0",
                    timeout=5
                )
                self.last_mode = 'stop'
        else:
            # Aktive Ladung
            log.debug("Aktive Batteriesteuerung vorhanden. Setze externe Steuerung.")
            if self.last_mode != 'charge':
                # Battery Charge AC - ON
                req.get_http_session().get(
                    f"http://{self.__ip_address}/api.php?set=command&type=20738&text1=3&text2=1",
                    timeout=5
                )
                # Battery Discharging - OFF
                req.get_http_session().get(
                    f"http://{self.__ip_address}/api.php?set=command&type=20738&text1=4&text2=0",
                    timeout=5
                )
                self.last_mode = 'charge'

    def power_limit_controllable(self) -> bool:
        return True


component_descriptor = ComponentDescriptor(configuration_factory=BatterXBatSetup)
