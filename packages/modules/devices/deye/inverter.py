#!/usr/bin/env python3
from typing import Dict, Union

from dataclass_utils import dataclass_from_dict
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount import SimCounter
from modules.common.store import get_inverter_value_store
from modules.devices.deye.config import DeyeInverterSetup


class DeyeInverter:
    def __init__(self, device_id: int, component_config: Union[Dict, DeyeInverterSetup]) -> None:
        self.component_config = dataclass_from_dict(DeyeInverterSetup, component_config)
        self.store = get_inverter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.__device_id = device_id
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="pv")

    def update(self, client: ModbusTcpClient_) -> None:
        unit = self.component_config.configuration.modbus_id

        device_type = client.read_holding_registers(0, ModbusDataType.INT_16, unit=unit)
        if device_type == 0x0200 or device_type == 0x0300:  # SINGLE_PHASE_STRING or SINGLE_PHASE_HYBRID
            power = sum(client.read_holding_registers(186, [ModbusDataType.INT_16]*4, unit=unit)) * -1
            exported = self.sim_counter.sim_count(power)[1]
        else:  # THREE_PHASE_LV (0x0500, 0x0005), THREE_PHASE_HV (0x0006)
            power = sum(client.read_holding_registers(672, [ModbusDataType.INT_16]*2, unit=unit)) * -1
            if device_type == 0x0006:  # THREE_PHASE_HV
                power = power * 10
            # 534: Gesamt Produktion Wechselrichter unsigned integer in kWh * 0,1
            exported = client.read_holding_registers(534, ModbusDataType.UINT_16, unit=unit) * 100

        inverter_state = InverterState(
            power=power,
            exported=exported,
        )
        self.store.set(inverter_state)


component_descriptor = ComponentDescriptor(configuration_factory=DeyeInverterSetup)
