#!/usr/bin/env python3
import logging
from typing import Tuple
from modules.common import modbus
from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.modbus import ModbusDataType, Endian
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store import get_bat_value_store
from modules.common.simcount._simcounter import SimCounter
from modules.devices.e3dc.e3dc.config import E3dcBatSetup


log = logging.getLogger(__name__)


def read_bat(client: modbus.ModbusTcpClient_, modbus_id: int) -> Tuple[int, int]:
    # 40082 SoC
    soc = client.read_holding_registers(40082, ModbusDataType.INT_16, unit=modbus_id)
    # 40069 Speicherleistung
    power = client.read_holding_registers(40069, ModbusDataType.INT_32, wordorder=Endian.Little, unit=modbus_id)
    return soc, power


class E3dcBat(AbstractBat):
    def __init__(self,
                 device_id: int,
                 component_config: E3dcBatSetup,
                 modbus_id: int) -> None:
        self.component_config = component_config
        self.__modbus_id = modbus_id
        # bat
        self.sim_counter = SimCounter(device_id, self.component_config.id, prefix="speicher")
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self, client: modbus.ModbusTcpClient_) -> None:

        soc, power = read_bat(client, self.__modbus_id)
        imported, exported = self.sim_counter.sim_count(power)
        bat_state = BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )
        self.store.set(bat_state)


component_descriptor = ComponentDescriptor(configuration_factory=E3dcBatSetup)
