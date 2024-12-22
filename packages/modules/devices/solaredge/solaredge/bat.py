#!/usr/bin/env python3
"""
Dieses Skript ermöglicht die optionale Steuerung von SolarEdge-Batterien über Modbus.
Für eine Fernsteuerung der Batterie muss der Wert des Registers StorageConf_CtrlMode (0xE004) auf "4" (Remote) gesetzt sein.
Die Steuerung erfolgt über das Setzen von Leistungsbegrenzungen, Abfrage des Ladezustands (SOC) und der Batterieleistung.
"""

import logging
from typing import Optional, Dict, Union

# Importiere notwendige Module und Klassen für die Modbus-Kommunikation
from pymodbus.payload import BinaryPayloadDecoder, BinaryPayloadBuilder
from pymodbus.constants import Endian
from dataclass_utils import dataclass_from_dict
from modules.common import modbus
from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.simcount import SimCounter
from modules.common.store import get_bat_value_store
from modules.devices.solaredge.solaredge.config import SolaredgeBatSetup

# Initialisiere den Logger für Debugging und Fehlerausgaben
log = logging.getLogger(__name__)

# Definiere eine Konfigurationsklasse für SolarEdge
class SolaredgeConfig:
    """
    Konfigurationsklasse für SolarEdge-Registeradressen.
    Diese Klasse zentralisiert Adressen, um Änderungen einfach umzusetzen.
    """

    def __init__(self):
        # Register für die Begrenzung der Lade-/Entladeleistung
        self.power_limit_register = 0xE010
        # Register für den Ladezustand der Batterie (State of Charge - SOC)
        self.soc_register = 0xE184
        # Register für die aktuelle Batterieleistung
        self.power_register = 0xE174

# Definiere die Hauptklasse für die SolarEdge-Batteriesteuerung
class SolaredgeBat(AbstractBat):
    """
    Klasse zur Steuerung eines SolarEdge-Batteriesystems.
    Ermöglicht das Lesen und Schreiben von Parametern über Modbus.
    """

    def __init__(self,
                 device_id: int,
                 component_config: Union[Dict, SolaredgeBatSetup],
                 tcp_client: modbus.ModbusTcpClient_,
                 config: SolaredgeConfig) -> None:
        """
        Initialisiert die SolarEdge-Batterie-Klasse.

        :param device_id: Eindeutige Geräte-ID für die Kommunikation.
        :param component_config: Konfigurationseinstellungen für die Batterie.
        :param tcp_client: Modbus-TCP-Client für die Kommunikation.
        :param config: Instanz der Konfigurationsklasse mit Registeradressen.
        """
        self.__device_id = device_id  # Geräte-ID
        # Wandelt die Konfiguration in ein Dataclass-Objekt um
        self.component_config = dataclass_from_dict(SolaredgeBatSetup, component_config)
        # Speichert den TCP-Client
        self.__tcp_client = tcp_client
        # Speichert die SolarEdge-Registerkonfiguration
        self.config = config
        # Simulationszähler für Batterieaktivitäten
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="speicher")
        # Initialisiert einen internen Speicher für Werte
        self.store = get_bat_value_store(self.component_config.id)
        # Initialisiert einen Fehlerzustand für die Batterie
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def set_power_limit(self, power_limit: Optional[float]) -> None:
        """
        Setzt die Leistungsbegrenzung für das Laden/Entladen.

        :param power_limit: Begrenzung in Watt (positiver Wert) oder None, um keine Begrenzung zu setzen.
        """
        # Modbus-ID und Register-Adresse
        unit = self.component_config.configuration.modbus_id
        register = self.config.power_limit_register

        try:
            # Standardwert für keine Begrenzung ist 0.0
            if power_limit is None:
                power_limit = 0.0
                log.debug("Keine Begrenzung angegeben. Begrenzung wird deaktiviert (0.0).")

            # Aktuellen Wert der Leistungsbegrenzung auslesen
            current_limit = self.get_power_limit()
            # Prüfen, ob der neue Wert gleich dem aktuellen ist
            if current_limit == power_limit:
                log.info(f"Leistungsbegrenzung bereits auf {current_limit} W gesetzt. Keine Änderung notwendig.")
                return

            # Vorbereitung zum Schreiben des neuen Wertes (Float32 im Big-Endian-Format)
            builder = BinaryPayloadBuilder(byteorder=Endian.Big, wordorder=Endian.Big)
            builder.add_32bit_float(power_limit)  # Füge den Wert hinzu
            registers = builder.to_registers()  # Konvertiere in Register-Daten

            # Schreibe den neuen Wert ins Modbus-Register
            self.__tcp_client.write_registers(register, registers, unit=unit)
            log.info(f"Leistungsbegrenzung erfolgreich auf {power_limit} W gesetzt.")
        except Exception as e:
            # Fehler beim Setzen der Begrenzung
            log.error(f"Fehler beim Setzen der Leistungsbegrenzung: {e}")
            raise

    def get_power_limit(self) -> Optional[float]:
        """
        Liest die aktuell eingestellte Leistungsbegrenzung.

        :return: Die aktuelle Begrenzung in Watt (Float32) oder None bei Fehler.
        """
        # Modbus-ID und Register-Adresse
        unit = self.component_config.configuration.modbus_id
        register = self.config.power_limit_register

        try:
            # Lese die aktuellen Registerwerte
            response = self.__tcp_client.read_holding_registers(register, count=2, unit=unit)
            if response.isError():
                # Fehler beim Lesen
                raise Exception(f"Fehler beim Lesen der Begrenzung aus Register {register}.")

            # Dekodiere den Wert (Float32 im Big-Endian-Format)
            decoder = BinaryPayloadDecoder.fromRegisters(
                response.registers, byteorder=Endian.Big, wordorder=Endian.Big
            )
            current_limit = decoder.decode_32bit_float()  # Dekodierter Wert
            log.debug(f"Aktuelle Begrenzung: {current_limit} W aus Register {register}")
            return current_limit
        except Exception as e:
            # Fehler beim Lesen
            log.error(f"Fehler beim Lesen der Leistungsbegrenzung: {e}")
            raise


# Beschreibung der Konfigurationskomponente (z. B. für externe Systeme)
component_descriptor = ComponentDescriptor(configuration_factory=SolaredgeBatSetup)
