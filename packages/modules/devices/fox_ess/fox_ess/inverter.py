#!/usr/bin/env python3
from typing import Dict, Union

from dataclass_utils import dataclass_from_dict
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.store import get_inverter_value_store
from modules.devices.fox_ess.fox_ess.config import FoxEssInverterSetup


class FoxEssInverter:
    def __init__(self, component_config: Union[Dict, FoxEssInverterSetup]) -> None:
        self.component_config = dataclass_from_dict(FoxEssInverterSetup, component_config)
        self.store = get_inverter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self, client: ModbusTcpClient_) -> None:
        unit = self.component_config.configuration.modbus_id
        # PV1 + PV2 Power
        power = sum([self.__tcp_client.read_holding_registers(
            reg, ModbusDataType.INT_16, unit=self.__modbus_id)
            for reg in [31002, 31005]]) * -1
        # Gesamt Produktion Wechselrichter unsigned integer in kWh * 0,1
        exported = client.read_holding_registers(32000, ModbusDataType.UINT_32, unit=unit) * 100

        inverter_state = InverterState(
            power=power,
            exported=exported,
        )
        self.store.set(inverter_state)


component_descriptor = ComponentDescriptor(configuration_factory=FoxEssInverterSetup)
