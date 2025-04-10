#!/usr/bin/env python3
from typing import TypedDict, Any

from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount import SimCounter
from modules.common.store import get_inverter_value_store
from modules.devices.deye.deye.config import DeyeInverterSetup
from modules.devices.deye.deye.device_type import DeviceType


class KwargsDict(TypedDict):
    device_id: int
    client: ModbusTcpClient_


class DeyeInverter(AbstractInverter):
    def __init__(self, component_config: DeyeInverterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.store = get_inverter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="pv")
        self.device_type = DeviceType(self.client.read_holding_registers(
            0, ModbusDataType.INT_16, unit=self.component_config.configuration.modbus_id))

    def update(self) -> None:
        unit = self.component_config.configuration.modbus_id

        if self.device_type == DeviceType.SINGLE_PHASE_STRING or self.device_type == DeviceType.SINGLE_PHASE_HYBRID:
            power = sum(self.client.read_holding_registers(186, [ModbusDataType.INT_16]*4, unit=unit)) * -1
            exported = self.sim_counter.sim_count(power)[1]

        else:  # THREE_PHASE_LV (0x0500, 0x0005), THREE_PHASE_HV (0x0006)
            power = sum(self.client.read_holding_registers(672, [ModbusDataType.INT_16]*2, unit=unit)) * -1

            if self.device_type == DeviceType.THREE_PHASE_HV:
                power = power * 10
            # 534: Gesamt Produktion Wechselrichter unsigned integer in kWh * 0,1
            exported = self.client.read_holding_registers(534, ModbusDataType.UINT_16, unit=unit) * 100

        inverter_state = InverterState(
            power=power,
            exported=exported,
        )
        self.store.set(inverter_state)


component_descriptor = ComponentDescriptor(configuration_factory=DeyeInverterSetup)
