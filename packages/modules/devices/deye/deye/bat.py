#!/usr/bin/env python3
import logging
from dataclass_utils import dataclass_from_dict
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount import SimCounter
from modules.common.store import get_bat_value_store
from modules.devices.deye.deye.config import DeyeBatSetup
from modules.devices.deye.deye.device_type import DeviceType

log = logging.getLogger(__name__)


class DeyeBat:
    def __init__(self, device_id: int, component_config: DeyeBatSetup) -> None:
        self.component_config = dataclass_from_dict(DeyeBatSetup, component_config)
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.__device_id = device_id
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="speicher")

    def update(self, client: ModbusTcpClient_, device_type: DeviceType) -> None:
        unit = self.component_config.configuration.modbus_id

        if device_type == DeviceType.THREE_PHASE:
            power = client.read_holding_registers(590, ModbusDataType.INT_16, unit=unit) * -1
            soc = client.read_holding_registers(588, ModbusDataType.INT_16, unit=unit)
            # 516: Geladen in kWh * 0,1
            imported = client.read_holding_registers(516, ModbusDataType.UINT_16, unit=unit) * 100
            # 518: Entladen in kWh * 0,1
            exported = client.read_holding_registers(518, ModbusDataType.UINT_16, unit=unit) * 100
        elif device_type == DeviceType.SINGLE_PHASE_STRING or device_type == DeviceType.SINGLE_PHASE_HYBRID:
            power = client.read_holding_registers(190, ModbusDataType.INT_16, unit=unit) * -1
            soc = client.read_holding_registers(184, ModbusDataType.INT_16, unit=unit)

            if device_type == DeviceType.SINGLE_PHASE_HYBRID:
                # 516: Geladen in kWh * 0,1
                imported = client.read_holding_registers(72, ModbusDataType.UINT_16, unit=unit) * 100
                # 518: Entladen in kWh * 0,1
                exported = client.read_holding_registers(74, ModbusDataType.UINT_16, unit=unit) * 100
            elif device_type == DeviceType.SINGLE_PHASE_STRING:
                imported, exported = self.sim_counter.sim_count(power)

        bat_state = BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )
        self.store.set(bat_state)


component_descriptor = ComponentDescriptor(configuration_factory=DeyeBatSetup)
