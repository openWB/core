#!/usr/bin/env python3
from typing import Dict, Union

from dataclass_utils import dataclass_from_dict
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.store import get_inverter_value_store
from modules.devices.solis.solis.config import SolisInverterSetup
from modules.devices.solis.solis.version import SolisVersion


class SolisInverter:
    def __init__(self, component_config: Union[Dict, SolisInverterSetup],
                 version: SolisVersion) -> None:
        self.component_config = dataclass_from_dict(SolisInverterSetup, component_config)
        self.store = get_inverter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.version = version

    def update(self, client: ModbusTcpClient_) -> None:
        unit = self.component_config.configuration.modbus_id

        if self.version == SolisVersion.inverter:
            power = client.read_holding_registers(3004, ModbusDataType.UINT_32, unit=unit) * -1
            # Unit 1kWh
            exported = client.read_holding_registers(3008, ModbusDataType.UINT_32, unit=unit) * 1000
        elif self.version == SolisVersion.hybrid:
            power = client.read_holding_registers(33057, ModbusDataType.UINT_32, unit=unit) * -1
            # Unit 1kWh
            exported = client.read_holding_registers(33029, ModbusDataType.UINT_32, unit=unit) * 1000

        inverter_state = InverterState(
            power=power,
            exported=exported
        )
        self.store.set(inverter_state)


component_descriptor = ComponentDescriptor(configuration_factory=SolisInverterSetup)
