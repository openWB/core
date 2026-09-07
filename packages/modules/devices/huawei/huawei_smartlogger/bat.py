#!/usr/bin/env python3
import logging
from typing import TypedDict, Any, Optional

from modules.common import modbus
from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType
from modules.common.simcount import SimCounter
from modules.common.store import get_component_value_store
from modules.devices.huawei.huawei_smartlogger.config import Huawei_SmartloggerBatSetup
from modules.common.utils.peak_filter import PeakFilter
from modules.common.component_type import ComponentType

log = logging.getLogger(__name__)


class KwargsDict(TypedDict):
    device_id: int
    tcp_client: modbus.ModbusTcpClient_


class Huawei_SmartloggerBat(AbstractBat):
    def __init__(self, component_config: Huawei_SmartloggerBatSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.__tcp_client: modbus.ModbusTcpClient_ = self.kwargs['tcp_client']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, self.component_config.type)
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.peak_filter = PeakFilter(ComponentType.BAT, self.component_config.id, self.fault_state)

    def update(self) -> None:
        modbus_id = self.component_config.configuration.modbus_id
        power = self.__tcp_client.read_holding_registers(37765, ModbusDataType.INT_32, unit=modbus_id)
        soc = self.__tcp_client.read_holding_registers(37760, ModbusDataType.INT_16, unit=modbus_id) / 10

        self.peak_filter.check_values(power)
        imported, exported = self.sim_counter.sim_count(power)
        bat_state = BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )
        self.store.set(bat_state)

    def set_power_limit(self, power_limit: Optional[int]) -> None:
        modbus_id = self.component_config.configuration.modbus_id
        if power_limit is None:
            log.debug("Keine Batteriesteuerung, Selbstregelung durch Speicher")
            if self.last_mode is not None:
                self.__tcp_client.write_register(47100, 0, data_type=ModbusDataType.UINT_16, unit=modbus_id)
                self.last_mode = None
        elif power_limit == 0:
            log.debug("Aktive Batteriesteuerung Huawei Smartlogger. Batterie wird auf Stop gesetzt und nicht entladen")
            if self.last_mode != 'stop':
                self.last_mode = 'stop'
            # discharge
            self.__tcp_client.write_register(47100, 2, data_type=ModbusDataType.UINT_16, unit=modbus_id)
            self.__tcp_client.write_register(47246, 0, data_type=ModbusDataType.UINT_16, unit=modbus_id)
            self.__tcp_client.write_register(47083, 1, data_type=ModbusDataType.UINT_16, unit=modbus_id)
            self.__tcp_client.write_register(47249, 0, data_type=ModbusDataType.UINT_16, unit=modbus_id)
        elif power_limit < 0:
            log.debug(f"Aktive Batteriesteuerung Huawei Smartlogger:"
                      f"Speicher soll mit {power_limit} W entladen werden.")
            if self.last_mode != 'discharge':
                self.last_mode = 'discharge'
            # discharge
            self.__tcp_client.write_register(47100, 2, data_type=ModbusDataType.UINT_16, unit=modbus_id)
            self.__tcp_client.write_register(47246, 0, data_type=ModbusDataType.UINT_16, unit=modbus_id)
            self.__tcp_client.write_register(47083, 1, data_type=ModbusDataType.UINT_16, unit=modbus_id)
            self.__tcp_client.write_register(47249, -power_limit, data_type=ModbusDataType.UINT_16, unit=modbus_id)
        elif power_limit > 0:
            log.debug(f"Aktive Batteriesteuerung Huawei Smartlogger:"
                      f"Speicher soll mit {power_limit} W geladen werden.")
            if self.last_mode != 'charge':
                self.last_mode = 'charge'
            # charge
            self.__tcp_client.write_register(47100, 1, data_type=ModbusDataType.UINT_16, unit=modbus_id)
            self.__tcp_client.write_register(47246, 0, data_type=ModbusDataType.UINT_16, unit=modbus_id)
            self.__tcp_client.write_register(47083, 1, data_type=ModbusDataType.UINT_16, unit=modbus_id)
            self.__tcp_client.write_register(47247, power_limit, data_type=ModbusDataType.UINT_16, unit=modbus_id)
            self.__tcp_client.write_register(47087, 1, data_type=ModbusDataType.UINT_16, unit=modbus_id)

    def power_limit_controllable(self) -> bool:
        return True


component_descriptor = ComponentDescriptor(configuration_factory=Huawei_SmartloggerBatSetup)
