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
    Orientiert am Original-Script, jedoch um erweiterte 
    Steuerungsfunktionen ergänzt (Remote Control, Power Limit etc.).
    """

    # Neue Register für Advanced-Steuerung:
    REMOTE_CONTROL_REGISTER = 57348       # soll auf 4 gesetzt werden
    ADVANCED_PWR_CTRL_REGISTER = 57740    # soll auf 1 stehen
    COMMIT_REGISTER = 57741              # auf 1 setzen, um Änderungen zu bestätigen
    DISCHARGE_LIMIT_REGISTER = 57360      # (FLOAT_32) Power-Limit

    def __init__(self,
                 device_id: int,
                 component_config: Union[Dict, SolaredgeBatSetup],
                 tcp_client: modbus.ModbusTcpClient_) -> None:
        self.__device_id = device_id
        self.component_config = dataclass_from_dict(SolaredgeBatSetup, component_config)
        self.__tcp_client = tcp_client

        # Prefix "speicher" wie im Original
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="speicher")
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> None:
        """
        Liest die aktuellen Werte (Power/SOC) und speichert 
        sie im ValueStore (unverändert aus dem Original).
        """
        self.store.set(self.read_state())

    def read_state(self) -> BatState:
        """
        Aus dem Original: ruft get_values() auf,
        berechnet import/export (sim_count) und gibt BatState zurück.
        """
        power, soc = self.get_values()
        imported, exported = self.get_imported_exported(power)
        return BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )

    def get_values(self) -> Tuple[float, float]:
        """
        Aus dem Original: Liest SOC/Power aus den Registern 
        62852 (SOC) und 62836 (Power). 
        Prüft nur power auf FLOAT32_UNSUPPORTED.
        """
        unit = self.component_config.configuration.modbus_id

        soc = self.__tcp_client.read_holding_registers(
            62852,
            ModbusDataType.FLOAT_32,
            wordorder=Endian.Little,
            unit=unit
        )
        power = self.__tcp_client.read_holding_registers(
            62836,
            ModbusDataType.FLOAT_32,
            wordorder=Endian.Little,
            unit=unit
        )

        # Falls der Wert für power nicht unterstützt wird:
        if power == FLOAT32_UNSUPPORTED:
            power = 0
        return power, soc

    def get_imported_exported(self, power: float) -> Tuple[float, float]:
        """
        Original-Funktion: verwendet sim_count, um 
        importierte/exportierte Energie zu bestimmen.
        """
        return self.sim_counter.sim_count(power)

    # -------------------------------------------------
    # Ab hier kommen die "neuen" Funktionen / Optimierungen
    # -------------------------------------------------

    def ensure_remote_control_mode(self, unit: int) -> bool:
        """
        Schaltet das Gerät in den Remote-Control-Modus (Register=4), 
        falls noch nicht geschehen, und macht einen Commit.
        """
        try:
            current_mode = self.__tcp_client.read_holding_registers(
                self.REMOTE_CONTROL_REGISTER, ModbusDataType.INT_16, unit=unit
            )
            if current_mode and len(current_mode) > 0 and current_mode[0] == 4:
                log.debug("Remote control mode is already enabled.")
                return True

            log.info("Enabling remote control mode.")
            builder = modbus.BinaryPayloadBuilder(byteorder=Endian.Big, wordorder=Endian.Little)
            builder.add_16bit_int(4)
            self.__tcp_client.write_registers(self.REMOTE_CONTROL_REGISTER, builder.to_registers(), unit=unit)

            self.commit_changes(unit)
            return True
        except Exception as e:
            log.error(f"Error enabling remote control mode: {e}")
            return False

    def ensure_advanced_power_control(self, unit: int) -> bool:
        """
        Prüft, ob der Advanced-Power-Control-Modus (Register=1) aktiv ist. 
        Ruft ggf. ensure_remote_control_mode() auf. 
        """
        if not self.ensure_remote_control_mode(unit):
            return False

        try:
            current_state = self.__tcp_client.read_holding_registers(
                self.ADVANCED_PWR_CTRL_REGISTER, ModbusDataType.INT_16, unit=unit
            )
            if current_state and len(current_state) > 0 and current_state[0] == 1:
                log.debug("Advanced power control is already enabled.")
                return True

            log.error("Advanced power control is not enabled. Please enable it or call activate_advanced_power_control().")
            return False
        except Exception as e:
            log.error(f"Error checking advanced power control: {e}")
            return False

    def activate_advanced_power_control(self, unit: int) -> None:
        """
        Aktiviert den Advanced-Power-Control-Modus (Register=1) 
        und committet die Änderung.
        """
        # Erst sicherstellen, dass Remote-Control aktiv ist
        if not self.ensure_remote_control_mode(unit):
            return

        try:
            builder = modbus.BinaryPayloadBuilder(byteorder=Endian.Big, wordorder=Endian.Little)
            builder.add_16bit_int(1)
            self.__tcp_client.write_registers(self.ADVANCED_PWR_CTRL_REGISTER, builder.to_registers(), unit=unit)
            log.debug("Advanced power control successfully activated.")

            self.commit_changes(unit)

            # Optionaler Readback-Check
            read_state = self.__tcp_client.read_holding_registers(
                self.ADVANCED_PWR_CTRL_REGISTER, ModbusDataType.INT_16, unit=unit
            )
            if read_state and len(read_state) > 0 and read_state[0] == 1:
                log.debug("Advanced power control confirmed active.")
            else:
                log.warning("Advanced power control activation not confirmed by readback.")
        except Exception as e:
            log.error(f"Error activating advanced power control: {e}")

    def commit_changes(self, unit: int) -> None:
        """
        Schreibt 1 in COMMIT_REGISTER, um Änderungen final zu übernehmen.
        """
        try:
            builder = modbus.BinaryPayloadBuilder(byteorder=Endian.Big, wordorder=Endian.Little)
            builder.add_16bit_int(1)
            self.__tcp_client.write_registers(self.COMMIT_REGISTER, builder.to_registers(), unit=unit)
            log.debug("Changes successfully committed.")
        except Exception as e:
            log.error(f"Error committing changes: {e}")

    def set_power_limit(self, power_limit: Optional[Union[int, float]]) -> None:
        """
        Setzt das Power-Limit (0..5000 W). Wenn None, dann Default 5000.
        Nutzt ensure_advanced_power_control() und ggf. activate_advanced_power_control().
        """
        unit = self.component_config.configuration.modbus_id

        # Prüfen, ob Advanced Power Control aktiv ist, sonst aktivieren.
        if not self.ensure_advanced_power_control(unit):
            self.activate_advanced_power_control(unit)

        # Standardwert
        if power_limit is None:
            power_limit = 5000

        if power_limit < 0 or power_limit > 5000:
            log.error(f"Invalid discharge limit: {power_limit}. Must be between 0 and 5000.")
            return

        try:
            current_limit = self.__tcp_client.read_holding_registers(
                self.DISCHARGE_LIMIT_REGISTER, ModbusDataType.FLOAT_32, unit=unit
            )
            already_set = (current_limit and len(current_limit) > 0 and current_limit[0] == power_limit)

            if already_set:
                log.info(f"Discharge limit already set to {power_limit} W. No action required.")
                return

            # Neuen Wert schreiben
            builder = modbus.BinaryPayloadBuilder(byteorder=Endian.Big, wordorder=Endian.Little)
            builder.add_32bit_float(float(power_limit))
            self.__tcp_client.write_registers(self.DISCHARGE_LIMIT_REGISTER, builder.to_registers(), unit=unit)
            log.debug(f"Discharge limit set to {power_limit} W.")

            self.commit_changes(unit)
        except Exception as e:
            log.error(f"Error setting discharge limit: {e}")


component_descriptor = ComponentDescriptor(configuration_factory=SolaredgeBatSetup)
