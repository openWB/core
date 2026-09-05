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
from modules.devices.saxpower.saxpower.config import SaxpowerBatSetup
from modules.common.utils.peak_filter import PeakFilter
from modules.common.component_type import ComponentType

log = logging.getLogger(__name__)


class KwargsDict(TypedDict):
    device_id: int
    client: modbus.ModbusTcpClient_
    modbus_id: int


class SaxpowerBat(AbstractBat):
    def __init__(self, component_config: SaxpowerBatSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.__tcp_client: modbus.ModbusTcpClient_ = self.kwargs['client']
        self.__modbus_id: int = self.kwargs['modbus_id']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, self.component_config.type)
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.peak_filter = PeakFilter(ComponentType.BAT, self.component_config.id, self.fault_state)

    def update(self) -> None:
        with self.__tcp_client:
            # Die beiden Register müssen zwingend zusammen ausgelesen werden, sonst scheitert die zweite Abfrage.
            soc, power = self.__tcp_client.read_holding_registers(46, [ModbusDataType.INT_16]*2, unit=self.__modbus_id)
            power = power * -1 + 16384
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
        unit = self.__modbus_id

        if power_limit is None:
            # Kein Powerlimit gefordert, erlaubte Entladeleistung auf Maximalwert setzen
            max_power = 4600
            log.debug("Saxpower: Keine Batteriesteuerung gefordert, deaktiviere externe Steuerung.")
            if self.last_mode is not None:
                self.__tcp_client.write_register(43, max_power, data_type=ModbusDataType.UINT_16, unit=unit)
                self.last_mode = None
        elif power_limit == 0:
            # Erlaubte Entladeleistung auf 0 setzen
            log.debug("Saxpower: Aktive Batteriesteuerung angestoßen. Setze Entladesperre.")
            if self.last_mode != 'stop':
                self.__tcp_client.write_register(43, 0, data_type=ModbusDataType.UINT_16, unit=unit)
                self.last_mode = 'stop'
        elif power_limit < 0:
            # Erlaubte Entladeleistung auf power_limit setzen
            log.debug("Saxpower: Aktive Batteriesteuerung angestoßen. Erlaubte Entladeleistung "
                      f"auf {power_limit}W setzen.")
            if self.last_mode != 'stop':
                self.__tcp_client.write_register(43, power_limit, data_type=ModbusDataType.UINT_16, unit=unit)
                self.last_mode = 'stop'
        else:
            # Aktive Ladung
            log.debug("Saxpower: Aktive Batterieladung nicht möglich. Setze stattdessen Entladesperre.")
            if self.last_mode != 'charge':
                self.__tcp_client.write_register(43, 0, data_type=ModbusDataType.UINT_16, unit=unit)
                self.last_mode = 'charge'

    def power_limit_controllable(self) -> bool:
        return True


component_descriptor = ComponentDescriptor(configuration_factory=SaxpowerBatSetup)
