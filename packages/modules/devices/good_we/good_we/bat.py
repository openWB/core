#!/usr/bin/env python3
from typing import TypedDict, Any, Optional
import logging

from modules.common import modbus
from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.modbus import ModbusDataType
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.simcount import SimCounter
from modules.common.store import get_bat_value_store
from modules.devices.good_we.good_we.config import GoodWeBatSetup
from modules.devices.good_we.good_we.version import GoodWeVersion

log = logging.getLogger(__name__)


class KwargsDict(TypedDict):
    device_id: int
    modbus_id: int
    version: GoodWeVersion
    firmware: int
    client: modbus.ModbusTcpClient_


class GoodWeBat(AbstractBat):
    def __init__(self, component_config: GoodWeBatSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.__modbus_id: int = self.kwargs['modbus_id']
        self.version: GoodWeVersion = self.kwargs['version']
        self.firmware: int = self.kwargs['firmware']
        self.__tcp_client: modbus.ModbusTcpClient_ = self.kwargs['client']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="speicher")
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.last_mode = 'Undefined'

    def update(self) -> None:
        battery_index = getattr(self.component_config.configuration, "battery_index", 1)
        with self.__tcp_client:
            if battery_index == 1:
                if self.version == GoodWeVersion.V_1_7:
                    power = self.__tcp_client.read_holding_registers(
                        35183, ModbusDataType.INT_16, unit=self.__modbus_id)*-1
                else:
                    power = self.__tcp_client.read_holding_registers(
                        35182, ModbusDataType.INT_32, unit=self.__modbus_id)*-1
                soc = self.__tcp_client.read_holding_registers(37007, ModbusDataType.UINT_16, unit=self.__modbus_id)
                imported = self.__tcp_client.read_holding_registers(
                    35206, ModbusDataType.UINT_32, unit=self.__modbus_id) * 100
                exported = self.__tcp_client.read_holding_registers(
                    35209, ModbusDataType.UINT_32, unit=self.__modbus_id) * 100
            else:
                power = self.__tcp_client.read_holding_registers(35264, ModbusDataType.INT_32, unit=self.__modbus_id)*-1
                soc = self.__tcp_client.read_holding_registers(39005, ModbusDataType.UINT_16, unit=self.__modbus_id)
                imported, exported = self.sim_counter.sim_count(power)

        bat_state = BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )
        self.store.set(bat_state)

    def set_power_limit(self, power_limit: Optional[int]) -> None:
        unit = self.__modbus_id
        log.debug(f'last_mode: {self.last_mode}')

        if power_limit is None:
            log.debug("Keine Batteriesteuerung, Selbstregelung durch Wechselrichter")
            if self.last_mode is not None:
                self.__tcp_client.write_register(47511, 1, data_type=ModbusDataType.UINT_16, unit=unit)
                self.__tcp_client.write_register(47512, 0, data_type=ModbusDataType.UINT_16, unit=unit)
                self.last_mode = None
        elif power_limit == 0:
            log.debug("Aktive Batteriesteuerung. Batterie wird auf Stop gesetzt und nicht entladen")
            if self.last_mode != 'stop':
                self.__tcp_client.write_register(47511, 2, data_type=ModbusDataType.UINT_16, unit=unit)
                self.__tcp_client.write_register(47512, 0, data_type=ModbusDataType.UINT_16, unit=unit)
                self.last_mode = 'stop'
        elif power_limit < 0:
            log.debug(f"Aktive Batteriesteuerung. Batterie wird mit {power_limit} W entladen für den Hausverbrauch")
            if self.last_mode != 'discharge':
                self.__tcp_client.write_register(47511, 3, data_type=ModbusDataType.UINT_16, unit=unit)
                self.last_mode = 'discharge'
            # Die maximale Entladeleistung begrenzen auf 5000W, maximaler Wertebereich Modbusregister.
            power_value = int(min(abs(power_limit), 10000))
            log.debug(f"Aktive Batteriesteuerung. Batterie wird mit {power_value} W entladen für den Hausverbrauch")
            self.__tcp_client.write_register(47512, power_value, data_type=ModbusDataType.UINT_16, unit=unit)
        elif power_limit > 0:
            if self.last_mode != 'charge':
                self.__tcp_client.write_register(47511, 2, data_type=ModbusDataType.UINT_16, unit=unit)
                self.last_mode = 'charge'
            power_value = int(min(abs(power_limit), 10000))
            log.debug(f"Aktive Batteriesteuerung. Batterie wird mit {power_value} W entladen für den Hausverbrauch")
            self.__tcp_client.write_register(47512, power_value, data_type=ModbusDataType.UINT_16, unit=unit)

    def power_limit_controllable(self) -> bool:
        return True


component_descriptor = ComponentDescriptor(configuration_factory=GoodWeBatSetup)
