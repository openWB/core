#!/usr/bin/env python3
from typing import Dict, Union

from dataclass_utils import dataclass_from_dict
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.store import get_inverter_value_store
from modules.devices.deye.config import DeyeInverterSetup


class DeyeInverter:
    def __init__(self, component_config: Union[Dict, DeyeInverterSetup]) -> None:
        self.component_config = dataclass_from_dict(DeyeInverterSetup, component_config)
        self.store = get_inverter_value_store(self.component_config.id)
        self.component_info = ComponentInfo.from_component_config(self.component_config)

    def update(self, client: ModbusTcpClient_) -> None:
        unit = self.component_config.configuration.modbus_id

        # Wechselrichter hat 2 mppt Tracker
        power_in1 = sum(client.read_holding_registers(672, ModbusDataType.INT_16, unit=unit))
        power_in2 = sum(client.read_holding_registers(673, ModbusDataType.INT_16, unit=unit))
        power = power_in1 + power_in2

        # 534: Gesamt Produktion Wechselrichter unsigned integer in kWh * 0,1
        exported = client.read_holding_registers(534, ModbusDataType.UINT_16, unit=unit) * 100

        inverter_state = InverterState(
            power=power,
            exported=exported,
        )
        self.store.set(inverter_state)


component_descriptor = ComponentDescriptor(configuration_factory=DeyeInverterSetup)
