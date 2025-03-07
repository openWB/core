#!/usr/bin/env python3
import logging
from typing import Dict, Tuple, Union

from pymodbus.constants import Endian

from dataclass_utils import dataclass_from_dict
from modules.common import modbus
from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType
from modules.common.simcount import SimCounter
from modules.common.store import get_bat_value_store
from modules.devices.solaredge.solaredge.config import SolaredgeBatSetup

log = logging.getLogger(__name__)

FLOAT32_UNSUPPORTED = -0xffffff00000000000000000000000000


class SolaredgeBat(AbstractBat):
    def __init__(self,
                 device_id: int,
                 component_config: Union[Dict, SolaredgeBatSetup],
                 tcp_client: modbus.ModbusTcpClient_) -> None:
        self.__device_id = device_id
        self.component_config = dataclass_from_dict(SolaredgeBatSetup, component_config)
        self.__tcp_client = tcp_client
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="speicher")
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> None:
        self.store.set(self.read_state())

    def read_state(self):
        power, soc = self.get_values()
        imported, exported = self.get_imported_exported(power)
        return BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )

    def get_values(self) -> Tuple[float, float]:
        unit = self.component_config.configuration.modbus_id
        # Use 1 as fallback if battery_index is not set
        battery_index = getattr(self.component_config.configuration, "battery_index", 1)

        # Define base registers for Battery 1 in hex
        base_soc_reg = 0xE184  # Battery 1 SoC
        base_power_reg = 0xE174  # Battery 1 Power
        offset = 0x100  # 256 bytes in hex

        # Adjust registers based on battery_index
        if battery_index == 1:
            soc_reg = base_soc_reg
            power_reg = base_power_reg
        elif battery_index == 2:
            soc_reg = base_soc_reg + offset  # 0xE284
            power_reg = base_power_reg + offset  # 0xE274
        else:
            raise ValueError(f"Invalid battery_index: {battery_index}. Must be 1 or 2.")

        # Read SoC and Power from the appropriate registers
        soc = self.__tcp_client.read_holding_registers(
            soc_reg, ModbusDataType.FLOAT_32, wordorder=Endian.Little, unit=unit
        )
        power = self.__tcp_client.read_holding_registers(
            power_reg, ModbusDataType.FLOAT_32, wordorder=Endian.Little, unit=unit
        )

        # Handle unsupported FLOAT32 case
        if power == FLOAT32_UNSUPPORTED:
            power = 0

        return power, soc

    def get_imported_exported(self, power: float) -> Tuple[float, float]:
        return self.sim_counter.sim_count(power)


component_descriptor = ComponentDescriptor(configuration_factory=SolaredgeBatSetup)
