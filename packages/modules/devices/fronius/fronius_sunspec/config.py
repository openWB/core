#!/usr/bin/env python3
from typing import List, Optional

from modules.common.component_setup import ComponentSetup
from modules.devices.fronius.fronius_sunspec.inv_version import FroniusInverterVersion
from ..vendor import vendor_descriptor


class FroniusSunspecConfiguration:
    def __init__(self, ip_address: Optional[str] = None, port: int = 502, counter_modbus_id: int = 200):
        self.ip_address = ip_address
        self.port = port
        # Modbus-Adresse ("Zähleradresse") des Smart Meters, zu finden auf der Weboberfläche des
        # Wechselrichters unter Kommunikation -> Modbus. Werkseinstellung laut Fronius: 200. Für
        # den Wechselrichter selbst ist die Modbus-Adresse bei Modbus TCP fest auf 1 definiert und
        # daher nicht konfigurierbar.
        self.counter_modbus_id = counter_modbus_id


class FroniusSunspec:
    def __init__(self,
                 name: str = "Fronius (Modbus/SunSpec)",
                 type: str = "fronius_sunspec",
                 id: int = 0,
                 configuration: FroniusSunspecConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or FroniusSunspecConfiguration()


class FroniusSunspecCounterConfiguration:
    def __init__(self):
        pass


class FroniusSunspecCounterSetup(ComponentSetup[FroniusSunspecCounterConfiguration]):
    def __init__(self,
                 name: str = "Fronius SunSpec Zähler",
                 type: str = "counter",
                 id: int = 0,
                 configuration: FroniusSunspecCounterConfiguration = None,
                 **kwargs) -> None:
        super().__init__(name, type, id, configuration or FroniusSunspecCounterConfiguration(), **kwargs)


class FroniusSunspecInverterConfiguration:
    def __init__(self,
                 version: FroniusInverterVersion = FroniusInverterVersion.mppt,
                 pv_mppt_indices: Optional[List[int]] = None):
        self.version = version
        # Nur für version=mppt relevant: welche MPPT-Kanäle (SunSpec-Modell 160, 1-indiziert)
        # PV-Strings sind. Auf Hybrid-Geräten belegen die Speicher-Lade-/Entladekanäle eigene,
        # höhere Indizes (siehe FroniusSunspecBatConfiguration.mppt_index) -- welche Indizes
        # tatsächlich PV vs. Speicher sind, unterscheidet sich zwischen Geräteserien und muss am
        # Gerät (Kanalbezeichnung im Fronius-Webinterface bzw. per Modbus-Tool) geprüft werden.
        self.pv_mppt_indices = pv_mppt_indices if pv_mppt_indices is not None else [1, 2]


class FroniusSunspecInverterSetup(ComponentSetup[FroniusSunspecInverterConfiguration]):
    def __init__(self,
                 name: str = "Fronius SunSpec Wechselrichter",
                 type: str = "inverter",
                 id: int = 0,
                 configuration: FroniusSunspecInverterConfiguration = None,
                 **kwargs) -> None:
        super().__init__(name, type, id, configuration or FroniusSunspecInverterConfiguration(), **kwargs)


class FroniusSunspecBatConfiguration:
    def __init__(self, mppt_index: Optional[int] = None):
        # MPPT-Kanal (SunSpec-Modell 160, 1-indiziert), der die tatsächliche Lade-/Entladeleistung
        # des Speichers liefert. None, falls unbekannt -- dann liefert die Komponente SOC und
        # Steuerung, aber keine Momentanleistung (power bleibt 0).
        self.mppt_index = mppt_index


class FroniusSunspecBatSetup(ComponentSetup[FroniusSunspecBatConfiguration]):
    def __init__(self,
                 name: str = "Fronius SunSpec Speicher",
                 type: str = "bat",
                 id: int = 0,
                 configuration: FroniusSunspecBatConfiguration = None,
                 **kwargs) -> None:
        super().__init__(name, type, id, configuration or FroniusSunspecBatConfiguration(), **kwargs)
