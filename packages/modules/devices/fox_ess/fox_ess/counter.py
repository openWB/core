from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.store import get_counter_value_store
from modules.devices.fox_ess.fox_ess.config import FoxEssCounterSetup
from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from typing import TypedDict, Any


class KwargsDict(TypedDict):
    client: ModbusTcpClient_


class FoxEssCounter(AbstractCounter):
    def __init__(self, component_config: FoxEssCounterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> None:
        unit = self.component_config.configuration.modbus_id

        powers = [val * -1 for val in
                  self.client.read_holding_registers(31026, [ModbusDataType.INT_16]*3, device_id=unit)]
        power = sum(powers)
        frequency = self.client.read_holding_registers(31015, ModbusDataType.UINT_16, device_id=unit) / 100
        imported = self.client.read_holding_registers(32018, ModbusDataType.UINT_32, device_id=unit) * 100
        exported = self.client.read_holding_registers(32015, ModbusDataType.UINT_32, device_id=unit) * 100

        counter_state = CounterState(
            imported=imported,
            exported=exported,
            power=power,
            powers=powers,
            frequency=frequency
        )
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=FoxEssCounterSetup)
