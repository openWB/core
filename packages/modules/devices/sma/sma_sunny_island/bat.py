#!/usr/bin/env python3
from typing import TypedDict, Any, Optional
import logging

from modules.common import modbus
from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType
from modules.common.store import get_bat_value_store
from modules.devices.sma.sma_sunny_island.config import SmaSunnyIslandBatSetup
from modules.common.utils.peak_filter import PeakFilter
from modules.common.component_type import ComponentType

log = logging.getLogger(__name__)


class KwargsDict(TypedDict):
    client: modbus.ModbusTcpClient_


class SunnyIslandBat(AbstractBat):
    def __init__(self, component_config: SmaSunnyIslandBatSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__tcp_client: modbus.ModbusTcpClient_ = self.kwargs['client']
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.peak_filter = PeakFilter(ComponentType.BAT, self.component_config.id, self.fault_state)
        self.last_mode = 'Undefined'

    def update(self) -> None:
        unit = self.component_config.configuration.modbus_id

        with self.__tcp_client:
            soc = self.__tcp_client.read_holding_registers(30845, ModbusDataType.INT_32, unit=unit)

            power = self.__tcp_client.read_holding_registers(30775, ModbusDataType.INT_32, unit=unit) * -1
            imported, exported = self.__tcp_client.read_holding_registers(30595, [ModbusDataType.INT_32]*2, unit=unit)

        imported, exported = self.peak_filter.check_values(power, imported, exported)
        return BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )
        self.store.set(bat_state)

    def set_power_limit(self, power_limit: Optional[int]) -> None:
        unit = self.component_config.configuration.modbus_id

        if power_limit is None:
            if self.last_mode is not None:
                # Kein Powerlimit gefordert, externe Steuerung war aktiv, externe Steuerung deaktivieren
                self.__tcp_client.write_register(40151, 803, data_type=ModbusDataType.UINT_32, unit=unit)
                self.__tcp_client.write_register(40149, 0, data_type=ModbusDataType.INT_32, unit=unit)
                log.debug("Keine Batteriesteuerung gefordert, deaktiviere externe Steuerung.")
                self.last_mode = None
        else:
            # Powerlimit gefordert, externe Steuerung aktivieren, Limit setzen
            self.__tcp_client.write_register(40151, 802, data_type=ModbusDataType.UINT_32, unit=unit)
            power_value = int(power_limit) * -1
            self.__tcp_client.write_register(40149, power_value, data_type=ModbusDataType.INT_32, unit=unit)
            log.debug("Aktive Batteriesteuerung vorhanden. Setze externe Steuerung. Angeforderte Leistung: {power_value}")
            self.last_mode = 'limited'

    def power_limit_controllable(self) -> bool:
        return True


component_descriptor = ComponentDescriptor(configuration_factory=SmaSunnyIslandBatSetup)
