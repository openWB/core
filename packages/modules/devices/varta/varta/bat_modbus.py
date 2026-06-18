#!/usr/bin/env python3
from typing import TypedDict, Any, Optional
import logging
import struct

from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount import SimCounter
from modules.common.store import get_bat_value_store
from modules.devices.varta.varta.config import VartaBatModbusSetup
from modules.common.utils.peak_filter import PeakFilter
from modules.common.component_type import ComponentType

log = logging.getLogger(__name__)


class KwargsDict(TypedDict):
    device_id: int
    modbus_id: int
    client: ModbusTcpClient_


class VartaBatModbus(AbstractBat):
    def __init__(self, component_config: VartaBatModbusSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.__modbus_id: int = self.kwargs['modbus_id']
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="speicher")
        self.store = get_bat_value_store(self.component_config.id)
        self.last_mode = 'Undefined'
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.peak_filter = PeakFilter(ComponentType.BAT, self.component_config.id, self.fault_state)

    def update(self) -> None:
        self.set_state(self.get_state())

    def get_state(self) -> BatState:
        soc = self.client.read_holding_registers(1068, ModbusDataType.INT_16, unit=self.__modbus_id)
        power = self.client.read_holding_registers(1066, ModbusDataType.INT_16, unit=self.__modbus_id)
        self.peak_filter.check_values(power)
        return BatState(
            power=power,
            soc=soc,
        )

    def set_state(self, state: BatState) -> None:
        state.imported, state.exported = self.sim_counter.sim_count(state.power)
        self.store.set(state)

    def set_power_limit(self, power_limit: Optional[int]) -> None:
        unit = self.__modbus_id
        log.debug(f'last_mode: {self.last_mode}')

        if power_limit is None:
            log.debug("Keine Batteriesteuerung, Selbstregelung durch Wechselrichter")
            if self.last_mode is not None:
                # hier muss die maximale Entladeleistung des Systems einmalig gesetzt werden
                # Wir nehmen default -4000W an. Nach 120s setzt sich das Register
                # automatisch zurück
                max_discharge_w = -4000
                uint16_value = struct.unpack(">H", struct.pack(">h", max_discharge_w))[0]
                self.client.write_register(1074, uint16_value, data_type=ModbusDataType.UINT_16, unit=unit)
                self.last_mode = None
        elif power_limit < 0:
            # Das Register muss kontinuierlich geschrieben werden, da der Speicher
            # sonst nach 120s die Steuerung aufhebt.
            log.debug(f"Aktive Batteriesteuerung. Batterie darf mit {power_limit} W entladen werden "
                      "für den Hausverbrauch")
            uint16_value = struct.unpack(">H", struct.pack(">h", power_limit))[0]
            self.client.write_register(1074, uint16_value, data_type=ModbusDataType.INT_16, unit=unit)
            self.last_mode = 'discharge'
        else:
            # Das Register muss kontinuierlich geschrieben werden, da der Speicher
            # sonst nach 120s die Steuerung aufhebt.
            if power_limit == 0:
                log.debug("Aktive Batteriesteuerung, Speicher wird auf Stop gesetzt.")
            else:
                log.debug(f"Aktive Batteriesteuerung, übergebene Leistung: {power_limit}W. "
                          "Aktive Ladung nicht möglich. Speicher wird auf Stop gesetzt.")

            self.client.write_register(1074, 0, data_type=ModbusDataType.INT_16, unit=unit)
            self.last_mode = 'stop'

    def power_limit_controllable(self) -> bool:
        return True


component_descriptor = ComponentDescriptor(configuration_factory=VartaBatModbusSetup)
