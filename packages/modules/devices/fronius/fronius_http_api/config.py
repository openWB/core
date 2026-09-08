#!/usr/bin/env python3
from enum import Enum
from typing import Optional

from modules.common.component_setup import ComponentSetup
from ..vendor import vendor_descriptor


class MeterLocation(Enum):
    # 0...grid interconnection point (primary meter)
    # positive power is consumption, negative is feed in
    grid = 0
    # 1...load (primary meter)
    # negative power is consumption, positive is production!
    load = 1
    # 3...external generator (secondary meters)(multiple)
    # negative power is consumption, positive is production!
    external = 3
    # 256-511 subloads (secondary meters)(unique)
    # negative power is consumption, positive us production!
    subload = 256

    @classmethod
    def get(self, value):
        return MeterLocation(256 if 256 <= value <= 511 else value)


class FroniusConfiguration:
    def __init__(self, ip_address: Optional[str] = None):
        self.ip_address = ip_address


class Fronius:
    def __init__(self,
                 name: str = "Fronius",
                 type: str = "fronius_http_api",
                 id: int = 0,
                 configuration: FroniusConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or FroniusConfiguration()


class FroniusBatConfiguration:
    def __init__(self,
                 meter_id: int = 0,
                 username: Optional[str] = None,
                 password: Optional[str] = None):
        self.meter_id = meter_id
        # Installateur-Zugangsdaten, nur für die aktive Speichersteuerung benötigt. Ohne sie wird der
        # Speicher weiterhin ausgelesen, kann aber nicht aktiv gesteuert werden.
        self.username = username
        self.password = password


class FroniusBatSetup(ComponentSetup[FroniusBatConfiguration]):
    def __init__(self,
                 name: str = "Fronius Speicher",
                 type: str = "bat",
                 id: int = 0,
                 configuration: FroniusBatConfiguration = None,
                 **kwargs) -> None:
        super().__init__(name, type, id, configuration or FroniusBatConfiguration(), **kwargs)


# Zähler ist im Wechselrichter integriert (S0), keine eigene SmartMeter-Hardware -- die Netz-Leistung
# wird aus der ohnehin für andere Komponenten abgerufenen PowerFlow-Antwort gelesen, meter_id ist dann
# ohne Bedeutung.
COUNTER_VARIANT_S0 = 3


class FroniusCounterConfiguration:
    def __init__(self, meter_id: int = 0, variant: int = 0):
        self.meter_id = meter_id
        self.variant = variant


class FroniusCounterSetup(ComponentSetup[FroniusCounterConfiguration]):
    def __init__(self,
                 name: str = "Fronius Zähler",
                 type: str = "counter",
                 id: int = 0,
                 configuration: FroniusCounterConfiguration = None,
                 **kwargs) -> None:
        super().__init__(name, type, id, configuration or FroniusCounterConfiguration(), **kwargs)


class FroniusInverterConfiguration:
    def __init__(self, secondary_id: Optional[int] = None):
        # None: primärer Wechselrichter (Site.P_PV der PowerFlow-Antwort).
        # gesetzt: sekundärer/companion Wechselrichter mit dieser ID (Body.Data.SecondaryMeters).
        self.secondary_id = secondary_id


class FroniusInverterSetup(ComponentSetup[FroniusInverterConfiguration]):
    def __init__(self,
                 name: str = "Fronius Wechselrichter",
                 type: str = "inverter",
                 id: int = 0,
                 configuration: FroniusInverterConfiguration = None,
                 **kwargs) -> None:
        super().__init__(name, type, id, configuration or FroniusInverterConfiguration(), **kwargs)


class FroniusProductionMeterConfiguration:
    def __init__(self, meter_id: int = 0, variant: int = 0):
        self.meter_id = meter_id
        self.variant = variant


class FroniusProductionMeterSetup(ComponentSetup[FroniusProductionMeterConfiguration]):
    def __init__(self,
                 name: str = "Fronius Erzeugerzähler",
                 type: str = "inverter_production_meter",
                 id: int = 0,
                 configuration: FroniusProductionMeterConfiguration = None,
                 **kwargs) -> None:
        super().__init__(name, type, id, configuration or FroniusProductionMeterConfiguration(), **kwargs)
