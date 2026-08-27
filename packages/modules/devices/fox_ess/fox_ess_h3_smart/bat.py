#!/usr/bin/env python3
import logging
from typing import TypedDict, Any, Optional

from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.simcount import SimCounter
from modules.common.store import get_component_value_store
from modules.devices.fox_ess.fox_ess_h3_smart.config import FoxEssH3SmartBatSetup
from modules.common.utils.peak_filter import PeakFilter
from modules.common.component_type import ComponentType

log = logging.getLogger(__name__)


class KwargsDict(TypedDict):
    device_id: int
    client: ModbusTcpClient_


class FoxEssH3SmartBat(AbstractBat):
    def __init__(self, component_config: FoxEssH3SmartBatSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.peak_filter = PeakFilter(ComponentType.BAT, self.component_config.id, self.fault_state)
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, self.component_config.type)

    def update(self) -> None:
        unit = self.component_config.configuration.modbus_id

        power = self.client.read_holding_registers(39237, ModbusDataType.INT_32, unit=unit)
        soc = self.client.read_holding_registers(37612, ModbusDataType.INT_16, unit=unit) / 100

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
        unit = self.component_config.configuration.modbus_id

        if power_limit is None:
            log.debug("Keine Batteriesteuerung, Selbstregelung durch Wechselrichter")
            if self.last_mode is not None:
                # remote control disabled, mode self use (1)
                self.__tcp_client.write_register(46001, 0, data_type=ModbusDataType.UINT_16, unit=unit)
                self.__tcp_client.write_register(49203, 1, data_type=ModbusDataType.UINT_16, unit=unit)
                self.last_mode = None
        elif power_limit == 0:
            # remote control enabled, watchdog 60s, active power 0W, mode FeedIn Priority (2)
            log.debug("Aktive Batteriesteuerung. FoxEss H3 Smart wird auf Stop gesetzt und nicht entladen")
            if self.last_mode != 'stop':
                self.__tcp_client.write_register(46001, 1, data_type=ModbusDataType.UINT_16, unit=unit)
                self.__tcp_client.write_register(46002, 60, data_type=ModbusDataType.UINT_16, unit=unit)
                self.__tcp_client.write_register(49203, 2, data_type=ModbusDataType.UINT_16, unit=unit)
                self.last_mode = 'stop'
            self.__tcp_client.write_register(46003, 0, data_type=ModbusDataType.UINT_16, unit=unit)
        elif power_limit < 0:
            # remote control enabled, watchdog 60s, active power 0W, mode Backup (3)
            log.debug(f"Aktive Batteriesteuerung FoxEss H3 Smart:"
                      f"Speicher soll mit {power_limit} W entladen werden")
            if self.last_mode != 'discharge':
                self.__tcp_client.write_register(46001, 1, data_type=ModbusDataType.UINT_16, unit=unit)
                self.__tcp_client.write_register(46002, 60, data_type=ModbusDataType.UINT_16, unit=unit)
                self.__tcp_client.write_register(49203, 3, data_type=ModbusDataType.UINT_16, unit=unit)
                self.last_mode = 'discharge'
            self.__tcp_client.write_register(46003, -power_limit, data_type=ModbusDataType.UINT_16, unit=unit)
        elif power_limit > 0:
            # remote control enabled, watchdog 60s, active power 0W, mode Backup (3)
            log.debug(f"Aktive Batteriesteuerung FoxEss H3 Smart:"
                      f"Speicher soll mit {power_limit} W geladen werden")
            if self.last_mode != 'charge':
                self.__tcp_client.write_register(46001, 1, data_type=ModbusDataType.UINT_16, unit=unit)
                self.__tcp_client.write_register(46002, 60, data_type=ModbusDataType.UINT_16, unit=unit)
                self.__tcp_client.write_register(49203, 3, data_type=ModbusDataType.UINT_16, unit=unit)
                self.last_mode = 'charge'
            self.__tcp_client.write_register(46003, -power_limit, data_type=ModbusDataType.UINT_16, unit=unit)

    def power_limit_controllable(self) -> bool:
        return True


component_descriptor = ComponentDescriptor(configuration_factory=FoxEssH3SmartBatSetup)
