#!/usr/bin/env python3
import logging
from dataclass_utils import dataclass_from_dict
from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount import SimCounter
from modules.common.store import get_bat_value_store
from modules.devices.mtec.mtec.config import MTecBatSetup

log = logging.getLogger(__name__)


class MTecBat(AbstractBat):
    def __init__(self, device_id: int, component_config: MTecBatSetup) -> None:
        self.component_config = dataclass_from_dict(MTecBatSetup, component_config)
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.__device_id = device_id
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="speicher")

    def update(self, client: ModbusTcpClient_) -> None:
        unit = self.component_config.configuration.modbus_id
        generation = self.component_config.configuration.generation

        if generation == 2:
            power = client.read_holding_registers(40258, ModbusDataType.INT_32, unit=unit) * -1
            # soc unit 0.01%
            soc = client.read_holding_registers(43000, ModbusDataType.UINT_16, unit=unit) / 100
        else:
            power = client.read_holding_registers(30258, ModbusDataType.INT_32, unit=unit) * -1
            soc = client.read_holding_registers(33000, ModbusDataType.UINT_16, unit=unit) / 100
        imported, exported = self.sim_counter.sim_count(power)

        bat_state = BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )
        self.store.set(bat_state)


component_descriptor = ComponentDescriptor(configuration_factory=MTecBatSetup)
