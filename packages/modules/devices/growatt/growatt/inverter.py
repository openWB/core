#!/usr/bin/env python3
from typing import TypedDict, Any

from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.simcount import SimCounter
from modules.common.utils.peak_filter import PeakFilter
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.store import get_component_value_store
from modules.devices.growatt.growatt.config import GrowattInverterSetup
from modules.devices.growatt.growatt.version import GrowattVersion
from modules.common.component_type import ComponentType


class KwargsDict(TypedDict):
    device_id: int
    modbus_id: int
    version: GrowattVersion
    client: ModbusTcpClient_


class GrowattInverter(AbstractInverter):
    def __init__(self, component_config: GrowattInverterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.__modbus_id: int = self.kwargs['modbus_id']
        self.version: GrowattVersion = self.kwargs['version']
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.peak_filter = PeakFilter(ComponentType.INVERTER, self.component_config.id, self.fault_state)
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, self.component_config.type)

    def update(self) -> None:
        if self.version == GrowattVersion.vpp:
            # Quelle: Growatt VPP Protocol V2.03, Input 31058 (PV-Gesamtleistung, int32, 0.1W).
            power = self.client.read_input_registers(31058, ModbusDataType.INT_32,
                                                     unit=self.__modbus_id) / -10
            self.peak_filter.check_values(power)
            imported, exported = self.sim_counter.sim_count(power)
        elif self.version == GrowattVersion.sph:
            # Quelle: Protocol II V1.39, Basisblock Input 0-124 (gemeinsam für alle Modellfamilien).
            power = self.client.read_input_registers(1, ModbusDataType.UINT_32,
                                                     unit=self.__modbus_id) / -10
            exported = self.client.read_input_registers(91, ModbusDataType.UINT_32,
                                                        unit=self.__modbus_id) * 100
            _, exported = self.peak_filter.check_values(power, None, exported)
            imported, _ = self.sim_counter.sim_count(power)
        else:  # GrowattVersion.tlx
            # Quelle: Protocol II V1.39, Bereich 3000-3124 (TL-X/TL-XH/TL3-XH).
            power = self.client.read_input_registers(3001, ModbusDataType.UINT_32,
                                                     unit=self.__modbus_id) / -10
            exported = self.client.read_input_registers(3053, ModbusDataType.UINT_32,
                                                        unit=self.__modbus_id) * 100
            _, exported = self.peak_filter.check_values(power, None, exported)
            imported, _ = self.sim_counter.sim_count(power)

        inverter_state = InverterState(
            power=power,
            imported=imported,
            exported=exported
        )
        self.store.set(inverter_state)


component_descriptor = ComponentDescriptor(configuration_factory=GrowattInverterSetup)
