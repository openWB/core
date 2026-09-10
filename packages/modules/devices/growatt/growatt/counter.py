#!/usr/bin/env python3
from typing import TypedDict, Any

from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.utils.peak_filter import PeakFilter
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.store import get_component_value_store
from modules.devices.growatt.growatt.config import GrowattCounterSetup
from modules.devices.growatt.growatt.version import GrowattVersion
from modules.common.component_type import ComponentType


class KwargsDict(TypedDict):
    modbus_id: int
    version: GrowattVersion
    client: ModbusTcpClient_


class GrowattCounter(AbstractCounter):
    def __init__(self, component_config: GrowattCounterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__modbus_id: int = self.kwargs['modbus_id']
        self.version: GrowattVersion = self.kwargs['version']
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.peak_filter = PeakFilter(ComponentType.COUNTER, self.component_config.id, self.fault_state)

    def update(self) -> None:
        if self.version == GrowattVersion.vpp:
            # Quelle: Growatt VPP Protocol V2.03, Input 31112 (int32, 0.1W).
            # Dort bereits: positiv = Bezug, negativ = Einspeisung - keine Invertierung nötig.
            power = self.client.read_input_registers(31112, ModbusDataType.INT_32,
                                                     unit=self.__modbus_id) * 0.1
            # VPP liefert keine separaten Phasenleistungen am Zähler (nur Summe 31112)
            powers = None

            exported = self.client.read_input_registers(31124, ModbusDataType.UINT_32,
                                                        unit=self.__modbus_id) * 100
            imported = self.client.read_input_registers(31120, ModbusDataType.UINT_32,
                                                        unit=self.__modbus_id) * 100

        elif self.version == GrowattVersion.sph:
            # Quelle: Protocol II V1.39, Storage-Block Input 1000-1249 (SPH/SPA-Hybrid).
            power_in = self.client.read_input_registers(1021, ModbusDataType.UINT_32,
                                                        unit=self.__modbus_id) * 0.1
            power_out = self.client.read_input_registers(1029, ModbusDataType.UINT_32,
                                                         unit=self.__modbus_id) * -0.1
            power = power_in + power_out

            powers = [
                self.client.read_input_registers(40, ModbusDataType.INT_32,
                                                 unit=self.__modbus_id) / 10,
                self.client.read_input_registers(44, ModbusDataType.INT_32,
                                                 unit=self.__modbus_id) / 10,
                self.client.read_input_registers(48, ModbusDataType.INT_32,
                                                 unit=self.__modbus_id) / 10]

            exported = self.client.read_input_registers(1050, ModbusDataType.UINT_32,
                                                        unit=self.__modbus_id) * 100
            imported = self.client.read_input_registers(1046, ModbusDataType.UINT_32,
                                                        unit=self.__modbus_id) * 100

        else:  # GrowattVersion.tlx
            # Quelle: Protocol II V1.39, Bereich 3000-3124 (TL-X/TL-XH/TL3-XH).
            # TL-X Dokumentation hat die gleichen Register wie die MAX Serie,
            # zusätzlich sind aber auch unten abweichende enthalten
            power_in = self.client.read_input_registers(3041, ModbusDataType.UINT_32,
                                                        unit=self.__modbus_id) * 0.1
            power_out = self.client.read_input_registers(3043, ModbusDataType.UINT_32,
                                                         unit=self.__modbus_id) * -0.1
            power = power_in + power_out

            powers = [
                self.client.read_input_registers(3028, ModbusDataType.INT_32,
                                                 unit=self.__modbus_id) / 10,
                self.client.read_input_registers(3032, ModbusDataType.INT_32,
                                                 unit=self.__modbus_id) / 10,
                self.client.read_input_registers(3036, ModbusDataType.INT_32,
                                                 unit=self.__modbus_id) / 10]

            exported = self.client.read_input_registers(3073, ModbusDataType.UINT_32,
                                                        unit=self.__modbus_id) * 100
            imported = self.client.read_input_registers(3069, ModbusDataType.UINT_32,
                                                        unit=self.__modbus_id) * 100

        imported, exported = self.peak_filter.check_values(power, imported, exported)
        counter_state = CounterState(
            imported=imported,
            exported=exported,
            power=power,
            powers=powers
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=GrowattCounterSetup)
