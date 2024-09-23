#!/usr/bin/env python3
from typing import Dict, Union

from dataclass_utils import dataclass_from_dict
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.store import get_bat_value_store
from modules.devices.qcells.qcells.config import QCellsBatSetup


class QCellsBat:
    def __init__(self,
                 component_config: Union[Dict, QCellsBatSetup],
                 modbus_id: int) -> None:
        self.__modbus_id = modbus_id
        self.component_config = dataclass_from_dict(QCellsBatSetup, component_config)
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self, client: ModbusTcpClient_) -> None:
        power = client.read_input_registers(0x0016, ModbusDataType.INT_16, unit=self.__modbus_id)
        soc = client.read_input_registers(0x001C, ModbusDataType.UINT_16, unit=self.__modbus_id)
        imported = client.read_input_registers(
            0x0021, ModbusDataType.UINT_16, unit=self.__modbus_id) * 100
        exported = client.read_input_registers(
            0x001D, ModbusDataType.UINT_16, unit=self.__modbus_id) * 100

        bat_state = BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )
        self.store.set(bat_state)


component_descriptor = ComponentDescriptor(configuration_factory=QCellsBatSetup)
