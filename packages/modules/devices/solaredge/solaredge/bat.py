#!/usr/bin/env python3
import logging
from typing import Dict, Tuple, Union, Optional

from pymodbus.constants import Endian

from dataclass_utils import dataclass_from_dict
from modules.common import modbus
from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType
from modules.common.simcount import SimCounter
from modules.common.store import get_bat_value_store
from modules.devices.solaredge.solaredge.config import SolaredgeBatSetup

log = logging.getLogger(__name__)


class SolaredgeBat(AbstractBat):
    def __init__(self,
                 device_id: int,
                 component_config: Union[Dict, SolaredgeBatSetup],
                 tcp_client: modbus.ModbusTcpClient_) -> None:
        self.__device_id = device_id
        self.component_config = dataclass_from_dict(SolaredgeBatSetup, component_config)
        self.__tcp_client = tcp_client
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="speicher")
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> None:
        self.store.set(self.read_state())

    def read_state(self) -> BatState:
        power, soc = self.get_values()
        imported, exported = self.sim_counter.sim_count(power)
        return BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )

    def get_values(self) -> Tuple[float, float]:
        unit = self.component_config.configuration.modbus_id
        soc = self.__tcp_client.read_holding_registers(
            57732, ModbusDataType.FLOAT_32, wordorder=Endian.Little, unit=unit)  # SOC Register
        power = self.__tcp_client.read_holding_registers(
            57716, ModbusDataType.FLOAT_32, wordorder=Endian.Little, unit=unit)  # Power Register
        return power, soc

    def set_power_limit(self, power_limit: Optional[int]) -> None:
        """
        Setzt die Leistungsbegrenzung für die Batterie.
        """
        DISCHARGE_LIMIT_REGISTER = 57360  # Discharge Limit Register
        unit = self.component_config.configuration.modbus_id

        if power_limit is None:
            log.debug("Kein Entladelimit vorgegeben, Batterie regelt selbst.")
            power_limit = 0  # Kein Limit
        else:
            log.debug(f'Setze Entladelimit auf: {power_limit} W.')

        self.__tcp_client.write_registers(
            DISCHARGE_LIMIT_REGISTER, power_limit, unit=unit)


component_descriptor = ComponentDescriptor(configuration_factory=SolaredgeBatSetup)
