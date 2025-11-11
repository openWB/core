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
from modules.devices.solarmax.solarmax.config import SolarmaxBatSetup

log = logging.getLogger(__name__)


class KwargsDict(TypedDict):
    device_id: int
    client: ModbusTcpClient_


class SolarmaxBat(AbstractBat):
    def __init__(self, component_config: SolarmaxBatSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="speicher")
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> None:
        unit = self.component_config.configuration.modbus_id
        power = self.client.read_input_registers(114, ModbusDataType.INT_32, unit=unit, wordorder=Endian.Little)
        soc = self.client.read_input_registers(122, ModbusDataType.INT_16, unit=unit)
        imported, exported = self.sim_counter.sim_count(power)

        bat_state = BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )
        self.store.set(bat_state)

    def set_power_limit(self, power_limit: Optional[int]) -> None:
        unit = self.component_config.configuration.modbus_id
        log.debug(f'last_mode: {self.last_mode}')
        # reg 142 is automatically reset every 60s so needs to be written continuously
        if power_limit is None:
            log.debug("Keine Batteriesteuerung, Selbstregelung durch Wechselrichter")
            if self.last_mode is not None:
                self.__tcp_client.write_registers(142, [0], data_type=ModbusDataType.INT_16, unit=unit)
                self.last_mode = None
        elif power_limit == 0:
            log.debug("Aktive Batteriesteuerung. Batterie wird auf Stop gesetzt und nicht entladen")
            self.__tcp_client.write_registers(140, [0], data_type=ModbusDataType.INT_16, unit=unit)
            self.__tcp_client.write_registers(141, [0], data_type=ModbusDataType.INT_16, unit=unit)
            self.__tcp_client.write_registers(142, [1], data_type=ModbusDataType.INT_16, unit=unit)
            self.last_mode = 'stop'
        elif power_limit < 0:
            log.debug(f"Aktive Batteriesteuerung. Batterie wird mit {power_limit} W entladen für den Hausverbrauch")
            self.__tcp_client.write_registers(142, [1], data_type=ModbusDataType.INT_16, unit=unit)
            self.last_mode = 'discharge'
            # Die maximale Entladeleistung begrenzen auf 5000W, maximaler Wertebereich Modbusregister.
            power_value = int(min(abs(power_limit), 7000))
            log.debug(f"Aktive Batteriesteuerung. Batterie wird mit {power_value} W entladen für den Hausverbrauch")
            self.__tcp_client.write_registers(140, [power_value], data_type=ModbusDataType.INT_16, unit=unit)
            self.__tcp_client.write_registers(141, [power_value], data_type=ModbusDataType.INT_16, unit=unit)

    def power_limit_controllable(self) -> bool:
        return True


component_descriptor = ComponentDescriptor(configuration_factory=SolarmaxBatSetup)
