#!/usr/bin/env python3
import logging
from typing import Any, Optional, TypedDict

from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, Endian, ModbusTcpClient_
from modules.common.simcount import SimCounter
from modules.common.store import get_bat_value_store
from modules.devices.sungrow.sungrow_ihm.config import SungrowIHMBatSetup, SungrowIHM

log = logging.getLogger(__name__)


class KwargsDict(TypedDict):
    client: ModbusTcpClient_
    device_config: SungrowIHM


class SungrowIHMBat(AbstractBat):
    def __init__(self, component_config: SungrowIHMBatSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.device_config: SungrowIHM = self.kwargs['device_config']
        self.__tcp_client: ModbusTcpClient_ = self.kwargs['client']
        self.sim_counter = SimCounter(self.device_config.id, self.component_config.id, prefix="speicher")
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.last_mode = 'Undefined'

    def update(self) -> None:
        unit = self.device_config.configuration.modbus_id
        soc = int(self.__tcp_client.read_input_registers(8162, ModbusDataType.UINT_16, unit=unit) / 10)

        bat_power = self.__tcp_client.read_input_registers(8160, ModbusDataType.INT_32,
                                                           wordorder=Endian.Little, unit=unit) * -10

        imported, exported = self.sim_counter.sim_count(bat_power)

        bat_state = BatState(
            power=bat_power,
            soc=soc,
            imported=imported,
            exported=exported
        )
        self.store.set(bat_state)

    def set_power_limit(self, power_limit: Optional[int]) -> None:
        unit = self.device_config.configuration.modbus_id
        log.debug(f'last_mode: {self.last_mode}')

        if power_limit is None:
            log.debug("Keine Batteriesteuerung, Selbstregelung durch Wechselrichter")
            if self.last_mode is not None:
                self.__tcp_client.write_registers(8023, [1], data_type=ModbusDataType.UINT_16, unit=unit)
                self.__tcp_client.write_registers(8024, [0xCC], data_type=ModbusDataType.UINT_16, unit=unit)
                self.last_mode = None
        elif power_limit == 0:
            log.debug("Aktive Batteriesteuerung. Batterie wird auf Stop gesetzt und nicht entladen")
            if self.last_mode != 'stop':
                self.__tcp_client.write_registers(8023, [5], data_type=ModbusDataType.UINT_16, unit=unit)
                self.__tcp_client.write_registers(8024, [0xCC], data_type=ModbusDataType.UINT_16, unit=unit)
                self.last_mode = 'stop'
        elif power_limit < 0:
            log.debug(f"Aktive Batteriesteuerung. Batterie wird mit {power_limit} W entladen für den Hausverbrauch")
            if self.last_mode != 'discharge':
                self.__tcp_client.write_registers(8023, [5], data_type=ModbusDataType.UINT_16, unit=unit)
                self.__tcp_client.write_registers(8024, [0xBB], data_type=ModbusDataType.UINT_16, unit=unit)
                self.last_mode = 'discharge'
            power_value = int(power_limit / 100)
            log.debug(f"Aktive Batteriesteuerung. Batterie wird mit {power_limit} W entladen für den Hausverbrauch")
            self.__tcp_client.write_registers(8025, [power_value], data_type=ModbusDataType.UINT_32,
                                              wordorder=Endian.Little, unit=unit)
        elif power_limit > 0:
            log.debug(f"Aktive Batteriesteuerung. Batterie wird mit {power_limit} W geladen")
            if self.last_mode != 'charge':
                self.__tcp_client.write_registers(8023, [5], data_type=ModbusDataType.UINT_16, unit=unit)
                self.__tcp_client.write_registers(8025, [0xAA], data_type=ModbusDataType.UINT_16, unit=unit)
                self.last_mode = 'charge'
            power_value = int(power_limit / 100)
            log.debug(f"Aktive Batteriesteuerung. Batterie wird mit {power_limit} W geladen")
            self.__tcp_client.write_registers(8025, [power_value], data_type=ModbusDataType.UINT_32,
                                              wordorder=Endian.Little, unit=unit)

    def power_limit_controllable(self) -> bool:
        return True


component_descriptor = ComponentDescriptor(configuration_factory=SungrowIHMBatSetup)
