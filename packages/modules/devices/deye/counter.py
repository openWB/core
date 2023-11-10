#!/usr/bin/env python3
from dataclass_utils import dataclass_from_dict
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.store import get_bat_value_store
from modules.devices.deye.config import DeyeBatSetup


class DeyeBat:
    def __init__(self, component_config: DeyeBatSetup) -> None:
        self.component_config = dataclass_from_dict(DeyeBatSetup, component_config)
        self.store = get_bat_value_store(self.component_config.id)
        self.component_info = ComponentInfo.from_component_config(self.component_config)

    def update(self, client: ModbusTcpClient_) -> None:
        unit = 1  # sollte dieser nicht aus der Konfiguration kommen; derWR könnte ja auch ID4 haben
        power = client.read_holding_registers(590, ModbusDataType.INT_16, unit=unit)
        soc = client.read_holding_registers(588, ModbusDataType.INT_16, unit=unit)
        # Geladen in Wh
        imported = client.read_holding_registers(516, ModbusDataType.INT_16, unit=unit)
        # Entladen in Wh
        exported = client.read_holding_registers(518, ModbusDataType.INT_16, unit=unit)

        bat_state = BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )
        self.store.set(bat_state)


component_descriptor = ComponentDescriptor(configuration_factory=DeyeBatSetup)
