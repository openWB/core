#!/usr/bin/env python3
import logging
from typing import TypedDict, Any, Optional
from pymodbus.constants import Endian

from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount import SimCounter
from modules.common.store import get_bat_value_store
from modules.devices.kostal.kostal_plenticore.config import KostalPlenticoreBatSetup

log = logging.getLogger(__name__)


class KwargsDict(TypedDict):
    device_id: int
    modbus_id: int
    endianess: Endian
    client: ModbusTcpClient_


class KostalPlenticoreBat(AbstractBat):
    def __init__(self, component_config: KostalPlenticoreBatSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.modbus_id: int = self.kwargs['modbus_id']
        self.endianess: Endian = self.kwargs['endianess']
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="speicher")
        self.last_mode = 'Undefined'

    def update(self) -> None:
        power = self.client.read_holding_registers(
            582, ModbusDataType.INT_16, unit=self.modbus_id, wordorder=self.endianess) * -1
        soc = self.client.read_holding_registers(
            514, ModbusDataType.INT_16, unit=self.modbus_id, wordorder=self.endianess)
        if power < 0:
            power = self.client.read_holding_registers(
                106, ModbusDataType.FLOAT_32, unit=self.modbus_id, wordorder=self.endianess) * -1
        imported, exported = self.sim_counter.sim_count(power)

        bat_state = BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )
        self.store.set(bat_state)

    # 0x40A 1034 Battery charge power (DC) setpoint, absolute -  W Float 2 RW
    # negative Werte: laden, positive Werte: entladen
    # Kostal setzt das Register autmatisch nach Timeout zurück auf Eigensteuerung.
    # Timeout kann im Kostal UI geändert werden. Standardwert 30s

    def set_power_limit(self, power_limit: Optional[int]) -> None:
        unit = self.modbus_id
        log.debug(f'last_mode: {self.last_mode}')

        if power_limit is None:
            # Wert wird nur einmal gesetzt damit die Eigenregelung nach Timeout greift
            log.debug("Keine Batteriesteuerung, Selbstregelung durch Wechselrichter")
            if self.last_mode is not None:
                self.client.write_registers(1034, [0], data_type=ModbusDataType.FLOAT_32, unit=unit)
                self.last_mode = None
        elif power_limit == 0:
            # wiederholt auf Stop setzen damit sich Register nicht zurücksetzt
            log.debug("Aktive Batteriesteuerung. Batterie wird auf Stop gesetzt und nicht entladen")
            self.client.write_registers(1034, [0], data_type=ModbusDataType.FLOAT_32, unit=unit)
            self.last_mode = 'stop'
        elif power_limit < 0:
            log.debug(f"Aktive Batteriesteuerung. Batterie wird mit {power_limit} W entladen für den Hausverbrauch")
            # Die maximale Entladeleistung begrenzen auf 7000W
            power_value = int(min(abs(power_limit), 7000)) * -1
            log.debug(f"Aktive Batteriesteuerung. Batterie wird mit {power_value} W entladen für den Hausverbrauch")
            self.client.write_registers(1034, [power_value], data_type=ModbusDataType.FLOAT_32, unit=unit)
            self.last_mode = 'discharge'

    def power_limit_controllable(self) -> bool:
        return True


component_descriptor = ComponentDescriptor(configuration_factory=KostalPlenticoreBatSetup)
