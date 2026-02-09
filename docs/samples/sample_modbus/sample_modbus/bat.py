#!/usr/bin/env python3
from enum import IntEnum
from typing import Optional, TypedDict, Any
from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount import SimCounter
from modules.common.store import get_component_value_store
from modules.devices.sample_modbus.sample_modbus.config import SampleBatSetup


class KwargsDict(TypedDict):
    device_id: int
    client: ModbusTcpClient_


class Register(IntEnum):
    CURRENT_L1 = 0x06
    POWER = 0x0C
    SOC = 0x46
    IMPORTED = 0x48
    EXPORTED = 0x4A


class SampleBat(AbstractBat):
    REG_MAPPING = (
        (Register.CURRENT_L1, [ModbusDataType.FLOAT_32]*3),
        (Register.POWER, [ModbusDataType.FLOAT_32]*3),
        (Register.SOC, ModbusDataType.FLOAT_32),
        (Register.IMPORTED, ModbusDataType.FLOAT_32),
        (Register.EXPORTED, ModbusDataType.FLOAT_32),
    )

    def __init__(self, component_config: SampleBatSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, self.component_config.type)
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> None:
        unit = self.component_config.configuration.modbus_id
        # Modbus-Bulk reader, liest einen Block von Registern und gibt ein Dictionary mit den Werten zurück
        # read_input_registers_bulk benötigit als Parameter das Startregister, die Anzahl der Register,
        # Register-Mapping und die Modbus-ID
        resp = self.client.read_input_registers_bulk(
            Register.CURRENT_L1, 70, mapping=self.REG_MAPPING, unit=self.id)
        bat_state = BatState(
            power=resp[Register.POWER],
            soc=resp[Register.SOC],
            imported=resp[Register.IMPORTED],
            exported=resp[Register.EXPORTED],
        )
        self.store.set(bat_state)

        # Einzelregister lesen (dauert länger, bei sehr weit >100 auseinanderliegenden Registern sinnvoll)
        power = self.client.read_holding_registers(reg, ModbusDataType.INT_32, unit=unit)
        soc = self.client.read_holding_registers(reg, ModbusDataType.INT_32, unit=unit)
        imported, exported = self.sim_counter.sim_count(power)

        bat_state = BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )
        self.store.set(bat_state)

    def set_power_limit(self, power_limit: Optional[int]) -> None:
        # Wenn der Speicher die Steuerung der Ladeleistung unterstützt, muss bei Übergabe einer Zahl auf aktive
        # Speichersteurung umgeschaltet werden, sodass der Speicher mit der übergebenen Leistung lädt/entlädt. Wird
        # None übergeben, muss der Speicher die Null-Punkt-Ausregelung selbst übernehmen.
        self.client.write_register(reg, power_limit)
        # Wenn der Speicher keine Steuerung der Ladeleistung unterstützt
        pass

    def power_limit_controllable(self) -> bool:
        # Wenn der Speicher die Steuerung der Ladeleistung unterstützt, muss True zurückgegeben werden.
        return True


component_descriptor = ComponentDescriptor(configuration_factory=SampleBatSetup)
