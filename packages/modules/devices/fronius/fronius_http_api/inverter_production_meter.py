#!/usr/bin/env python3
import logging
from typing import Dict, Optional, TypedDict, Any

from modules.common import req
from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.simcount import SimCounter
from modules.common.store import get_component_value_store
from modules.devices.fronius.fronius_http_api import meter_reader
from modules.devices.fronius.fronius_http_api.config import FroniusConfiguration, MeterLocation
from modules.devices.fronius.fronius_http_api.config import FroniusProductionMeterSetup
from modules.common.utils.peak_filter import PeakFilter
from modules.common.component_type import ComponentType

log = logging.getLogger(__name__)


class KwargsDict(TypedDict):
    device_id: int
    device_config: FroniusConfiguration


class FroniusProductionMeter(AbstractInverter):
    def __init__(self, component_config: FroniusProductionMeterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.device_config: FroniusConfiguration = self.kwargs['device_config']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, self.component_config.type)
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.peak_filter = PeakFilter(ComponentType.INVERTER, self.component_config.id, self.fault_state)
        self.cache_key = f"{self.component_config.type}_{self.component_config.id}"

    def update(self, meter_system_response: Optional[Dict] = None) -> None:
        config = self.component_config.configuration
        meter = meter_reader.read_meter(
            req.get_http_session(), self.device_config.ip_address, config.meter_id, config.variant,
            self.cache_key, meter_system_response)

        if meter.location == MeterLocation.grid:
            raise ValueError("Fehler: Dieser Zähler ist kein Erzeugerzähler.")

        # Für alle zulässigen Einbauorte (load/external/subload) meldet die Fronius-API laut Solar API V1
        # Dokumentation (4.8.6/4.8.7) positive Werte für Erzeugung -- openWBs Konvention ist umgekehrt
        # (negativ = Erzeugung, siehe inverter.py), daher wird hier immer invertiert.
        power = meter.power_sum * -1
        currents = [meter.powers[i] / meter.voltages[i] for i in range(0, 3)]

        self.peak_filter.check_values(power)
        _, exported = self.sim_counter.sim_count(power)

        self.store.set(InverterState(
            currents=currents,
            power=power,
            exported=exported
        ))


component_descriptor = ComponentDescriptor(configuration_factory=FroniusProductionMeterSetup)
