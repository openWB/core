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
        if soc is None or power is None:
            log.error("Ungueltige Werte aus den Modbus-Registern gelesen.")
            return BatState(power=0, soc=0, imported=0, exported=0)
        imported, exported = self.sim_counter.sim_count(power)
        log.debug(f"Gelesen - Power: {power}, SOC: {soc}")
        return BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )

    def get_values(self) -> Tuple[Optional[float], Optional[float]]:
        unit = self.component_config.configuration.modbus_id
        try:
            soc = self.__tcp_client.read_holding_registers(
                57732, ModbusDataType.FLOAT_32, wordorder=Endian.Little, unit=unit)  # SOC Register
            power = self.__tcp_client.read_holding_registers(
                57716, ModbusDataType.FLOAT_32, wordorder=Endian.Little, unit=unit)  # Power Register
            return power, soc
        except Exception as e:
            log.error(f"Fehler beim Lesen von Modbus-Registern: {e}")
            return None, None

    def set_power_limit(self, power_limit: Optional[int]) -> None:
    # Setzt die Leistungsbegrenzung für die Batterie.
    # - Bei None wird die Null-Punkt-Ausregelung aktiviert, Standardwert 5000 W.
    # - Bei Übergabe einer Zahl wird die Begrenzung entsprechend gesetzt.
    # - Schreibt den Wert nur, wenn er vom bestehenden Limit abweicht.

    DISCHARGE_LIMIT_REGISTER = 57360  # Discharge Limit Register
    unit = self.component_config.configuration.modbus_id

    # Logik bei None
    if power_limit is None:
        log.debug("Null-Punkt-Ausregelung aktiviert, Entladelimit wird auf 5000 W gesetzt.")
        power_limit = 5000  # Maximale Entladeleistung

    # Validierung für übergebene Werte
    elif power_limit < 0 or power_limit > 5000:
        log.error(f"Ungültiges Entladelimit: {power_limit}. Muss zwischen 0 und 5000 liegen.")
        return

    try:
        # Bestehendes Limit lesen
        current_limit = self.__tcp_client.read_holding_registers(
            DISCHARGE_LIMIT_REGISTER, ModbusDataType.FLOAT_32, unit=unit)

        # Nur schreiben, wenn der neue Wert vom bestehenden abweicht
        if current_limit == power_limit:
            log.info(f"Entladelimit ist bereits auf {current_limit} W gesetzt. Kein Schreiben erforderlich.")
            return

        # Neuen Wert schreiben
        self.__tcp_client.write_registers(
            DISCHARGE_LIMIT_REGISTER, [float_32(power_limit)], unit=unit)
        log.debug(f"Entladelimit erfolgreich auf {power_limit} W gesetzt.")

    except Exception as e:
        log.error(f"Fehler beim Setzen des Entladelimits: {e}")

component_descriptor = ComponentDescriptor(configuration_factory=SolaredgeBatSetup)
