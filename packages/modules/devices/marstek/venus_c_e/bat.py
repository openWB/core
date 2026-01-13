#!/usr/bin/env python3
from typing import Optional, TypedDict, Any, Union
from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount import SimCounter
from modules.common.store import get_component_value_store
from modules.devices.marstek.venus_c_e.config import VenusCEBatSetup


class KwargsDict(TypedDict):
    device_id: int
    client: ModbusTcpClient_


class VenusCEBat(AbstractBat):
    def __init__(self, component_config: VenusCEBatSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="speicher")
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def _read_reg(self, addr: int, type_: ModbusDataType) -> Union[int, float]:
        return self.client.read_holding_registers(addr, type_, unit=self.component_config.configuration.modbus_id)

    def _write_reg(self, addr: int, val: int) -> None:
        # Marstek Venus does not work with write_registers!
        self.client._delegate.write_register(addr, val, unit=self.component_config.configuration.modbus_id)

    def update(self) -> None:
        power = -self._read_reg(32202, ModbusDataType.INT_32)
        soc = self._read_reg(32104, ModbusDataType.UINT_16)

        # Marstek Venus has internal counter but it's buggy, hence we cannot use it
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
        if (power_limit is None):
            self._write_reg(42000, 0x55bb)
        else:
            self._write_reg(42000, 0x55aa)
            if power_limit < 0:
                self._write_reg(42010, 2)
                self._write_reg(42021, int(min(-power_limit, 2500)))
            elif power_limit > 0:
                self._write_reg(42010, 1)
                self._write_reg(42020, int(min(power_limit, 2500)))
            else:
                self._write_reg(42010, 0)

    def power_limit_controllable(self) -> bool:
        # Wenn der Speicher die Steuerung der Ladeleistung unterstützt, muss True zurückgegeben werden.
        return True


component_descriptor = ComponentDescriptor(configuration_factory=VenusCEBatSetup)
