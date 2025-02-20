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

FLOAT32_UNSUPPORTED = -0xffffff00000000000000000000000000


class SolaredgeBat(AbstractBat):
    """
    Klasse zur Verwaltung der Solaredge-Batteriesteuerung.
    Beinhaltet Funktionen zur Überwachung und Steuerung.
    """

    REMOTE_CONTROL_REGISTER = 57348  # Aktivierung von Remote Control
    ADVANCED_PWR_CTRL_REGISTER = 57740  # Aktivierung des erweiterten Leistungsmodus
    COMMIT_REGISTER = 57741  # Bestätigung von Änderungen
    DISCHARGE_LIMIT_REGISTER = 57360  # Leistungsbegrenzung in Watt

    def __init__(
        self, device_id: int, component_config: Union[Dict, SolaredgeBatSetup], tcp_client: modbus.ModbusTcpClient_
    ) -> None:
        """
        Initialisiert die Batteriesteuerung.
        """
        self.__device_id = device_id
        self.component_config = dataclass_from_dict(SolaredgeBatSetup, component_config)
        self.__tcp_client = tcp_client
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="speicher")
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> None:
        """
        Aktualisiert den aktuellen Batteriestatus und speichert ihn im Value Store.
        """
        try:
            self.store.set(self.read_state())
        except Exception:
            log.exception("Fehler beim Aktualisieren des Batterie-Status")
            self.fault_state.set_fault("Batterie-Status konnte nicht aktualisiert werden")

    def read_state(self) -> BatState:
        """
        Liest den aktuellen Zustand der Batterie und gibt ihn als BatState zurück.
        """
        try:
            power, soc = self.get_values()
            imported, exported = self.get_imported_exported(power)
            return BatState(power=power, soc=soc, imported=imported, exported=exported)
        except Exception:
            log.exception("Fehler beim Lesen des Batterie-Zustands")
            self.fault_state.set_fault("Fehler beim Lesen des Batterie-Zustands")
            return BatState(power=0, soc=0, imported=0, exported=0)

    def get_values(self) -> Tuple[float, float]:
        """
        Liest SOC und Leistung aus den entsprechenden Modbus-Registern.
        """
        unit = self.component_config.configuration.modbus_id
        try:
            soc = self.__tcp_client.read_holding_registers(
                62852, ModbusDataType.FLOAT_32, wordorder=Endian.Little, unit=unit
            )
            power = self.__tcp_client.read_holding_registers(
                62836, ModbusDataType.FLOAT_32, wordorder=Endian.Little, unit=unit
            )
            if power is None or len(power) == 0 or power[0] == FLOAT32_UNSUPPORTED:
                power = 0
            return power, soc
        except Exception:
            log.exception("Fehler beim Abrufen der Werte aus den Registern")
            return 0, 0

    def get_imported_exported(self, power: float) -> Tuple[float, float]:
        """
        Berechnet importierte und exportierte Energie basierend auf der aktuellen Leistung.
        """
        return self.sim_counter.sim_count(power)

    def ensure_remote_control_mode(self, unit: int) -> bool:
        """
        Aktiviert den Remote Control Modus, falls nicht bereits aktiv.
        """
        try:
            current_mode = self.__tcp_client.read_holding_registers(
                self.REMOTE_CONTROL_REGISTER, ModbusDataType.INT_16, unit=unit
            )
            if current_mode and len(current_mode) > 0 and current_mode[0] == 4:
                log.debug("Remote control mode is already enabled.")
                return True
            log.info("Enabling remote control mode.")
            self.__tcp_client.write_registers(self.REMOTE_CONTROL_REGISTER, [4], unit=unit)
            self.commit_changes(unit)
            return True
        except Exception:
            log.exception("Error enabling remote control mode")
            return False

    def commit_changes(self, unit: int) -> None:
        """
        Bestätigt Änderungen durch Schreiben in das COMMIT-Register.
        """
        try:
            self.__tcp_client.write_registers(self.COMMIT_REGISTER, [1], unit=unit)
        except Exception:
            log.exception("Error committing changes")

    def set_power_limit(self, power_limit: Optional[Union[int, float]]) -> None:
        """
        Setzt das Entladeleistungs-Limit der Batterie innerhalb eines gültigen Bereichs.
        """
        unit = self.component_config.configuration.modbus_id
        if not self.ensure_remote_control_mode(unit):
            return
        if power_limit is None:
            power_limit = 5000
        if power_limit < 0 or power_limit > 5000:
            log.error(f"Invalid discharge limit: {power_limit}. Must be between 0 and 5000.")
            return
        try:
            self.__tcp_client.write_registers(self.DISCHARGE_LIMIT_REGISTER, [int(power_limit)], unit=unit)
            self.commit_changes(unit)
        except Exception:
            log.exception("Error setting discharge limit")


component_descriptor = ComponentDescriptor(configuration_factory=SolaredgeBatSetup)
