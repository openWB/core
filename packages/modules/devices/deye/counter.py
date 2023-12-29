#!/usr/bin/env python3
from dataclass_utils import dataclass_from_dict
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount import SimCounter
from modules.common.store import get_counter_value_store
from modules.devices.deye.config import DeyeCounterSetup
from modules.devices.deye.device_type import DeviceType


class DeyeCounter:
    def __init__(self, device_id: int, component_config: DeyeCounterSetup) -> None:
        self.component_config = dataclass_from_dict(DeyeCounterSetup, component_config)
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.__device_id = device_id
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="bezug")

    def update(self, client: ModbusTcpClient_, device_type: DeviceType):
        unit = self.component_config.configuration.modbus_id

        if device_type == DeviceType.THREE_PHASE:
            currents = [c / 100 for c in client.read_holding_registers(613, [ModbusDataType.INT_16]*3, unit=unit)]
            voltages = [v / 10 for v in client.read_holding_registers(644, [ModbusDataType.INT_16]*3, unit=unit)]
            powers = client.read_holding_registers(616, [ModbusDataType.INT_16]*3, unit=unit)
            power = sum(powers)
            frequency = client.read_holding_registers(187, ModbusDataType.INT_32, unit=unit) * 100

            # Wenn der Import/export Netz in wh gerechnet wird => *100 !! kommt in kw/h *0.1
            imported = client.read_holding_registers(522, ModbusDataType.INT_16, unit=unit) * 100
            exported = client.read_holding_registers(524, ModbusDataType.INT_16, unit=unit) * 100

        elif device_type == DeviceType.SINGLE_PHASE_STRING or device_type == DeviceType.SINGLE_PHASE_HYBRID:
            frequency = client.read_holding_registers(79, ModbusDataType.INT_16, unit=unit) * 100

            if device_type == DeviceType.SINGLE_PHASE_HYBRID:
                powers = [0]*3
                currents = [0]*3
                voltages = [0]*3
                power = [0]
                # High und low word vom import sind nicht in aufeinanderfolgenden Registern
                imported, exported = self.sim_counter.sim_count(power)
            elif device_type == DeviceType.SINGLE_PHASE_STRING:
                currents = [c / 100 for c in client.read_holding_registers(76, [ModbusDataType.INT_16]*3, unit=unit)]
                voltages = [v / 10 for v in client.read_holding_registers(70, [ModbusDataType.INT_16]*3, unit=unit)]
                powers = [currents[i] * voltages[i] for i in range(0, 3)]
                power = sum(powers)
                imported, exported = self.sim_counter.sim_count(power)

        counter_state = CounterState(
            currents=currents,
            imported=imported,
            exported=exported,
            power=power,
            powers=powers,
            voltages=voltages,
            frequency=frequency
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=DeyeCounterSetup)
