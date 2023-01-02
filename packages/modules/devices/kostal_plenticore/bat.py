#!/usr/bin/env python3
import logging
from typing import Any, Callable
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.modbus import ModbusDataType
from modules.common.fault_state import ComponentInfo
from modules.common.simcount import SimCounter
from modules.common.store import get_bat_value_store
from modules.devices.kostal_plenticore.config import KostalPlenticoreBatSetup

log = logging.getLogger(__name__)


class KostalPlenticoreBat:
    def __init__(self,
                 device_id: int,
                 component_config: KostalPlenticoreBatSetup) -> None:
        self.component_config = component_config
        self.store = get_bat_value_store(self.component_config.id)
        self.sim_counter = SimCounter(device_id, self.component_config.id, prefix="speicher")
        self.component_info = ComponentInfo.from_component_config(self.component_config)

    def read_state(self, reader: Callable[[int, ModbusDataType], Any]) -> BatState:
        power = reader(582, ModbusDataType.INT_16) * -1
        soc = reader(514, ModbusDataType.INT_16)
        imported, exported = self.sim_counter.sim_count(power)
        log.debug("raw bat power "+str(power))
        # Speicherladung muss durch Wandlungsverluste und internen Verbrauch korrigiert werden, sonst
        # wird ein falscher Hausverbrauch berechnet. Die Verluste fallen hier unter den Tisch.
        if power < 0:
            power = reader(106, ModbusDataType.FLOAT_32) * -1

        return BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported,
        )

    def update(self, state):
        self.store.set(state)


component_descriptor = ComponentDescriptor(configuration_factory=KostalPlenticoreBatSetup)
